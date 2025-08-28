import time
from typing import Optional, Tuple
import requests
import ccxt

FX_API = "https://api.exchangerate.host/latest"

class LiveData:
    def __init__(self, exchange_id: str = "binance", symbol: str = "BTC/USDT"):
        self.exchange_id = exchange_id
        self.symbol = symbol
        self.exchange = getattr(ccxt, exchange_id)({
            "enableRateLimit": True,
        })

    def fetch_price(self) -> Optional[float]:
        """Fetch latest mid/last price via ccxt REST polling."""
        try:
            ticker = self.exchange.fetch_ticker(self.symbol)
            # prefer 'last'; fallback to 'bid'/'ask' mid
            last = ticker.get("last")
            if last is not None:
                return float(last)
            bid = ticker.get("bid")
            ask = ticker.get("ask")
            if bid and ask:
                return (bid + ask) / 2.0
        except Exception as e:
            # You might want to log e
            return None
        return None

def fetch_fx_rate(base: str = "USD", quote: str = "USD") -> float:
    """
    Return FX rate to convert from base -> quote.
    If base == quote, returns 1.0
    """
    if base.upper() == quote.upper():
        return 1.0
    params = {"base": base.upper(), "symbols": quote.upper()}
    try:
        r = requests.get(FX_API, params=params, timeout=7)
        r.raise_for_status()
        data = r.json()
        rate = data.get("rates", {}).get(quote.upper())
        if rate:
            return float(rate)
    except Exception:
        pass
    return 1.0  # fallback
