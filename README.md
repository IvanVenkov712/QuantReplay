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
- use all-in/all-out, fixed-share, or percentage-based position sizing with an optional cash buffer;
- track cash, positions, trades, orders, and portfolio value;
- calculate return, volatility, Sharpe ratio, drawdown, and trade metrics;
- compare a strategy against a benchmark on the same market data;
- configure CLI runs from TOML with explicit CLI-over-file precedence.

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

Comparison output shows every common metric in three value columns: the
strategy result, the benchmark result, and the difference calculated as
`strategy - benchmark`.

Use a local CSV file instead of Yahoo Finance:

```powershell
python -m backtester.cli backtest --source csv --csv-path data/SPY.csv --symbol SPY --start 2024-01-01 --end 2025-01-01
```

Include a 0.1% proportional commission and 0.05% slippage:

```powershell
python -m backtester.cli backtest --commission-model proportional --commission-rate 0.001 --slippage-rate 0.0005
```

Use a TOML configuration file:

```powershell
python -m backtester.cli backtest --config quantreplay.example.toml
```

If `--config` is omitted, the CLI automatically uses `quantreplay.toml` from
the current working directory when that file exists. Settings follow
`CLI option > TOML option > application default`, so individual file values
can be overridden for one run. See the
[`quantreplay.example.toml`](quantreplay.example.toml) file and the
[TOML configuration reference](docs/configuration.md) for the schema,
validation rules, and path behavior.

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
value compared with buying the asset once and holding it. The comparison table
keeps the two underlying metric values visible alongside their difference, so
the size and direction of that difference can be interpreted in context.

## Position sizing

Position sizing converts a signal into a whole-share order quantity.

| CLI name | Behavior |
| --- | --- |
| `all-in-all-out` | Buys the maximum affordable whole shares and sells the entire position. |
| `fixed` | Uses explicit buy and sell share quantities. |
| `percent` | Uses a fraction of available cash for buys and a fraction of owned shares for sells. |

All-in/all-out is the default. Percentage sizing does not target a
percentage of total portfolio equity. Because the engine supports only whole
shares, a valid sizing decision can produce a quantity of zero.

The optional `--buffer-rate` limits buy quantities so that the configured
fraction of current cash remains unspent, while sell quantities still follow
the selected policy. For example, `--buffer-rate 0.05` reserves 5% of cash.
When configured, `BufferQuantityResolver` wraps the base `QuantityResolver`.
Both use the same `BuyQuantityCapper`, which includes configured commission
and adverse slippage when checking how many shares fit within the budget.

## Backtesting assumptions

The engine separates signal generation from execution to avoid look-ahead
bias:

1. The strategy receives only candles available through candle `T`.
2. A signal generated from candle `T` creates an order intent without a
   quantity.
3. At candle `T+1` open, the position size is calculated using the current
   portfolio and the opening price supplied by the selected data source.
4. Slippage adjusts the fill price against the trader: BUY fills move up and
   SELL fills move down.
5. Commission is calculated from the resulting fill and deducted from cash.
6. Portfolio value is recorded at each candle's close.

The broker is long-only. Overnight price gaps affect all-in and percentage
order quantities because sizing happens at the execution open. Fixed-size
orders can be rejected when cash or shares are insufficient.

Yahoo Finance candles use adjusted OHLC prices. Dividends and stock splits are
therefore embedded in the price series, with distributions implicitly treated
as reinvested instead of being credited to portfolio cash. CSV prices are used
as supplied; callers are responsible for choosing a consistent adjusted or
unadjusted convention. See [Market data](docs/data.md) for the consequences of
these conventions.

The default is zero slippage with no commission. A fixed commission is charged
once per executed trade. A proportional commission is a fraction of trade
notional (`quantity * fill price`). Rates use decimal fractions, so `0.001`
means `0.1%`.

All-in and percentage BUY quantities are resolved against a budget that
already includes the configured commission and adverse slippage. Fixed BUY
instructions remain exact and can be rejected when unaffordable unless a
`--buffer-rate` is supplied; with a buffer, fixed quantities are capped to the
affordable amount. A failed order remains visible in the backtest result, but
it does not create a trade or change the portfolio. The CLI displays
individual rejection details when there are at most 10 rejected orders; above
that limit, it displays the rejection count without listing every order.

## Documentation

- [TOML configuration](docs/configuration.md): precedence, paths, complete file
  structure, supported keys, and validation
- [CLI reference](docs/cli.md): commands, parameters, sizing, and execution-cost
  options
- [Market data](docs/data.md): Yahoo Finance behavior, CSV format, and validation
- [Performance metrics](docs/metrics.md): formulas, interpretations, and edge cases

## Running tests

Run the test suite from the repository root:

```powershell
pytest
```
