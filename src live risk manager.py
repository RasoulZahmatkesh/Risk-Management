import argparse
import os
import time
from datetime import datetime
from typing import Optional

from risk_manager import RiskInput, recommend_units
from live_feed import LiveData, fetch_fx_rate

def human(n: float, digits: int = 6) -> str:
    try:
        return f"{float(n):,.{digits}f}"
    except Exception:
        return str(n)

def main():
    ap = argparse.ArgumentParser(description="Live Crypto Risk & Position Sizer")
    ap.add_argument("--exchange", default="binance", help="ccxt exchange id (default: binance)")
    ap.add_argument("--symbol", default="BTC/USDT", help="trading symbol (e.g., BTC/USDT)")
    ap.add_argument("--equity", type=float, required=True, help="account equity in USD (quote)")
    ap.add_argument("--leverage", type=float, required=True, help="leverage, e.g., 75")
    ap.add_argument("--entry", type=float, required=True, help="planned entry price")
    ap.add_argument("--side", choices=["long", "short"], required=True, help="long or short")
    ap.add_argument("--stop", type=float, default=None, help="optional stop loss price")
    ap.add_argument("--risk", type=float, default=0.02, help="risk percent of equity (0.02 = 2%)")
    ap.add_argument("--interval", type=float, default=2.0, help="refresh interval seconds")
    ap.add_argument("--display-currency", default="USD", help="convert metrics to this currency (default USD)")
    ap.add_argument("--quote-currency", default="USD", help="equity base currency (default USD)")
    args = ap.parse_args()

    ld = LiveData(exchange_id=args.exchange, symbol=args.symbol)

    print("\nStarting Live Risk Manager… Press Ctrl+C to exit.\n")
    print(f"Exchange: {args.exchange} | Symbol: {args.symbol} | Side: {args.side.upper()}")
    print(f"Equity: {args.equity} {args.quote_currency} | Leverage: {args.leverage}x | Entry: {args.entry}")
    if args.stop:
        print(f"Stop Loss: {args.stop}")
    print("")

    while True:
        try:
            live = ld.fetch_price()
            fx = fetch_fx_rate(base=args.quote_currency, quote=args.display_currency)

            if live is None:
                print("[WARN] Could not fetch live price. Retrying…")
                time.sleep(args.interval)
                continue

            inp = RiskInput(
                equity_usd=args.equity,      # treat as in quote currency; name kept from USD
                entry=args.entry,
                leverage=args.leverage,
                side=args.side,              # "long" or "short"
                stop_loss=args.stop,
                risk_percent=args.risk
            )

            res = recommend_units(inp, live_price=live)

            # convert margin and equity for display if needed
            eq_disp = args.equity * fx
            margin_unit_disp = res["margin_per_unit"] * fx
            rec_margin_disp = res["recommended_margin_capital"] * fx

            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            print("=" * 86)
            print(f"{now}  |  Live: {human(live, 2)}   Entry: {human(res['entry'],2)}   Side: {res['side'].upper()}   Lvg: {res['leverage']}x")
            print(f"Equity: {human(eq_disp,2)} {args.display_currency}   FX({args.quote_currency}->{args.display_currency}): {human(fx,4)}")
            print("-" * 86)
            print(f"Liquidation Price (approx): {human(res['liquidation_price'], 2)}")
            if args.stop:
                print(f"Per-Unit Risk to Stop: {human(res['per_unit_risk'], 2)}")
                print(f"Units by Risk (<= {args.risk*100:.1f}% equity): {human(res['units_by_risk'], 4)}")
            print(f"Margin per Unit: {human(res['margin_per_unit'], 2)}  ({human(margin_unit_disp,2)} {args.display_currency})")
            print(f"Max Units by Margin: {human(res['max_units_by_margin'], 4)}")
            print(f"Recommended Units: {human(res['recommended_units'], 4)}")
            print(f"Recommended Margin Capital: {human(res['recommended_margin_capital'], 2)} "
                  f"({human(rec_margin_disp,2)} {args.display_currency})")
            print("=" * 86)

            time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nExiting. Stay safe 🤝")
            break
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(args.interval)

if __name__ == "__main__":
    main()
