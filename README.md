# Crypto Risk Manager (Live)

A lightweight, terminal-based position sizer for crypto futures that updates live using `ccxt` for prices and a free FX endpoint for currency conversion. It computes liquidation, margin per unit, max units by margin, and risk-based recommended units (if a stop loss is provided) in real time.

> ⚠️ Educational tool only. Approximates isolated liquidation and *ignores maintenance margin, fees, funding, and exchange-specific nuances*. Always verify with your exchange’s exact formulas.
 Features
- Live price updates via `ccxt` (polling)
- Optional *stop loss* to size position by risk (e.g., 2% of equity)
- Live *FX conversion* (e.g., USD → EUR) for displayed amounts
- Clean CLI output; configurable refresh interval
 Install

git clone https://github.com/YourUsername/crypto-risk-manager.git
cd crypto-risk-manager
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
