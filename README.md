# QuantReplay

QuantReplay is a Python backtesting project for experimenting with simple
trading strategies on historical OHLCV market data. It is designed to show how
a backtesting engine, strategies, portfolio accounting, trade execution, and
performance metrics fit together without hiding the core logic inside a large
external framework.

It is an educational project, not a live trading bot or investment advice.

## Features

QuantReplay can:

- load historical candle data from Yahoo Finance or CSV files;
- validate and normalize OHLCV data before running a backtest;
- generate buy, sell, or hold signals from several strategies;
- execute generated orders on the next candle's open;
- model adverse slippage and zero, fixed, or proportional commissions;
- use all-in/all-out, fixed-share, or percentage-based position sizing;
- track cash, positions, trades, orders, and portfolio value;
- calculate return, volatility, Sharpe ratio, drawdown, and trade metrics;
- compare a strategy against a benchmark on the same market data.

## Installation

QuantReplay requires Python 3.12 or later. Install it from the repository root
in editable mode:

```powershell
python -m pip install -e .
```

This installs the package and its runtime dependencies (`pandas`,
`typing-extensions`, and `yfinance`). Editable mode makes changes under `src`
available without reinstalling the package.

For development, install the optional test dependencies as well:

```powershell
python -m pip install -e ".[dev]"
```

## Quick start

Run the default moving-average crossover strategy on five years of daily SPY
data:

```powershell
python -m backtester.cli backtest
```

Compare a strategy with buy and hold:

```powershell
python -m backtester.cli compare --strategy moving-average --benchmark buy-and-hold --symbol SPY
```

Use a local CSV file instead of Yahoo Finance:

```powershell
python -m backtester.cli backtest --source csv --csv-path data/SPY.csv --symbol SPY --start 2024-01-01 --end 2025-01-01
```

Include a 0.1% proportional commission and 0.05% slippage:

```powershell
python -m backtester.cli backtest --commission-model proportional --commission-rate 0.001 --slippage-rate 0.0005
```

See the [CLI reference](docs/cli.md) for all commands, options, and output
examples.

## Strategies

The CLI runs one selected strategy at a time. The `compare` command evaluates
that strategy and a benchmark using the same symbol, date range, data source,
initial capital, position-sizing policy, commission model, and slippage rate.

| CLI name | Class | Buy signal | Sell signal |
| --- | --- | --- | --- |
| `moving-average` | `MovingAverageCrossStrategy` | The short moving average crosses above the long moving average. | The short moving average crosses below the long moving average. |
| `buy-and-hold` | `BuyAndHoldStrategy` | The first time the strategy is called. | Never. |
| `rsi` | `SimpleRSIStrategy` | RSI falls below the minimum threshold. | RSI rises above the maximum threshold. |
| `mean-reversion` | `MeanReversionStrategy` | The current close is below the configured fraction of its recent average. | The current close reaches or exceeds the recent average. |

The default strategy is `MovingAverageCrossStrategy(20, 50)`. The default
benchmark is `BuyAndHoldStrategy`, which shows whether an active strategy added
value compared with buying the asset once and holding it.

## Position sizing

Position sizing converts a signal into a whole-share order quantity.

| CLI name | Class | Behavior |
| --- | --- | --- |
| `all-in-all-out` | `AllInAllOutSizer` | Buys the maximum affordable whole shares and sells the entire position. |
| `fixed` | `FixedSizer` | Uses explicit buy and sell share quantities. |
| `percent` | `PercentSizer` | Uses a fraction of available cash for buys and a fraction of owned shares for sells. |

`AllInAllOutSizer` is the default. Percentage sizing does not target a
percentage of total portfolio equity. Because the engine supports only whole
shares, a valid sizing decision can produce a quantity of zero.

## Backtesting assumptions

The engine separates signal generation from execution to avoid look-ahead
bias:

1. The strategy receives only candles available through candle `T`.
2. A signal generated from candle `T` creates an order intent without a
   quantity.
3. At candle `T+1` open, the position size is calculated using the current
   portfolio and the unadjusted opening price.
4. Slippage adjusts the fill price against the trader: BUY fills move up and
   SELL fills move down.
5. Commission is calculated from the resulting fill and deducted from cash.
6. Portfolio value is recorded at each candle's close.

The broker is long-only. Overnight price gaps affect all-in and percentage
order quantities because sizing happens at the execution open. Fixed-size
orders can be rejected when cash or shares are insufficient.

The default is zero slippage with no commission. A fixed commission is charged
once per executed trade. A proportional commission is a fraction of trade
notional (`quantity * fill price`). Rates use decimal fractions, so `0.001`
means `0.1%`.

Position sizing does not reserve cash for commission or adverse slippage. In
particular, an `all-in-all-out` BUY can be rejected as unaffordable when either
cost is non-zero. The failed order remains visible in the backtest result, but
it does not create a trade or change the portfolio.

## Documentation

- [CLI reference](docs/cli.md): commands, parameters, sizing, and execution-cost
  options
- [Market data](docs/data.md): Yahoo Finance behavior, CSV format, and validation
- [Performance metrics](docs/metrics.md): formulas, interpretations, and edge cases

## Running tests

Run the test suite from the repository root:

```powershell
pytest
```
