from dataclasses import dataclass
from typing import Optional, Literal
import math

Side = Literal["long", "short"]

@dataclass
class RiskInput:
    equity_usd: float          # total account equity in USD (or quote currency)
    entry: float               # entry price
    leverage: float            # e.g., 75
    side: Side                 # "long" or "short"
    stop_loss: Optional[float] = None  # optional stop price for risk sizing
    risk_percent: float = 0.02         # fraction of equity to risk (e.g., 0.02 = 2%)

def liquidation_price(entry: float, leverage: float, side: Side) -> float:
    """
    Simplified isolated-margin liquidation approximation (ignores maintenance margin & fees).
    long:  L = entry * (1 - 1/leverage)
    short: L = entry * (1 + 1/leverage)
    """
    if leverage <= 0:
        raise ValueError("leverage must be positive")
    if side == "long":
        return entry * (1 - 1.0 / leverage)
    return entry * (1 + 1.0 / leverage)

def margin_per_unit(entry: float, leverage: float) -> float:
    if leverage <= 0:
        raise ValueError("leverage must be positive")
    return entry / leverage

def max_units_affordable(equity_usd: float, entry: float, leverage: float) -> float:
    mpu = margin_per_unit(entry, leverage)
    if mpu <= 0:
        return 0.0
    # allow fractional contracts (for perp crypto you often can size to decimals)
    return equity_usd / mpu

def per_unit_risk(entry: float, stop_loss: float, side: Side) -> float:
    if stop_loss is None:
        return 0.0
    if side == "long":
        return max(0.0, entry - stop_loss)
    else:
        return max(0.0, stop_loss - entry)

def safe_units_by_risk(equity_usd: float, risk_percent: float, pu_risk: float) -> float:
    """
    Units such that (units * per_unit_risk) <= (equity * risk_percent)
    Returns fractional units allowed by risk.
    """
    risk_dollar = equity_usd * max(0.0, risk_percent)
    if pu_risk <= 0:
        # if no stop provided, return 0 from risk perspective
        return 0.0
    return risk_dollar / pu_risk

def recommend_units(inp: RiskInput, live_price: float) -> dict:
    """
    Given current live price, compute:
    - liquidation price
    - margin per unit
    - max units by margin
    - safe units by risk (if stop provided)
    - capital to use (margin) for recommended units
    """
    liq = liquidation_price(inp.entry, inp.leverage, inp.side)
    mpu = margin_per_unit(inp.entry, inp.leverage)
    max_by_margin = max_units_affordable(inp.equity_usd, inp.entry, inp.leverage)

    # per-unit risk based on provided stop loss (preferred)
    pu_risk = per_unit_risk(inp.entry, inp.stop_loss, inp.side)

    # choose recommended units as the minimum of "risk-based" and "margin-based" caps
    units_by_risk = safe_units_by_risk(inp.equity_usd, inp.risk_percent, pu_risk)
    candidates = [max_by_margin]
    if units_by_risk > 0:
        candidates.append(units_by_risk)

    rec_units = min(candidates) if candidates else 0.0

    # ensure we’re not sizing into instant liquidation (sanity check)
    # If live is beyond liquidation boundary for that side, recommend zero.
    if (inp.side == "long" and live_price <= liq) or (inp.side == "short" and live_price >= liq):
        rec_units = 0.0

    capital_margin = rec_units * mpu

    # P&L per unit relative to target or current price could be computed upstream if needed
    return {
        "entry": inp.entry,
        "live_price": live_price,
        "side": inp.side,
        "leverage": inp.leverage,
        "equity_usd": inp.equity_usd,
        "stop_loss": inp.stop_loss,
        "risk_percent": inp.risk_percent,
        "liquidation_price": liq,
        "margin_per_unit": mpu,
        "max_units_by_margin": max_by_margin,
        "per_unit_risk": pu_risk,
        "units_by_risk": units_by_risk,
        "recommended_units": rec_units,
        "recommended_margin_capital": capital_margin,
    }
