import yfinance as yf

data = yf.download(
    "SPY",
    start="2021-01-01",
    end="2026-01-01",
    interval="1d",
    auto_adjust=False,
)

data.to_csv("data/SPY.csv")