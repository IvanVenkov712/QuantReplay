import yfinance as yf

data = yf.download(
    "SPY",
    start="2021-01-01",
    end="2026-01-01",
    interval="1d",
    auto_adjust=False,
    multi_level_index=False,
)

data.to_csv("data/SPY.csv")

data = yf.download(
    "AAPL",
    start="2021-01-01",
    end="2026-01-01",
    interval="1d",
    auto_adjust=False,
    multi_level_index=False,
)

data.to_csv("data/AAPL.csv")

data = yf.download(
    "MSFT",
    start="2021-01-01",
    end="2026-01-01",
    interval="1d",
    auto_adjust=False,
    multi_level_index=False,
)

data.to_csv("data/MSFT.csv")