# QuantReplay

QuantReplay is a Python backtesting project for experimenting with simple trading strategies on historical OHLCV market data. The project is educational: it is meant to show how a backtesting engine, strategies, portfolio accounting, trade execution, and performance metrics fit together without hiding the core logic inside a large external framework.

It is not a live trading bot and it is not investment advice. The goal is to make backtesting mechanics understandable and testable.

## What the project does

QuantReplay can:

- load historical candle data from Yahoo Finance or from CSV files;
- validate OHLCV data before it is used by the engine;
- convert market data rows into `Candle` objects;
- run a single-symbol backtest with a strategy, broker, and portfolio;
- generate buy, sell, or hold signals from strategies;
- execute generated orders on the next candle's open;
- track cash, positions, trades, orders, and portfolio value;
- calculate performance metrics such as total return, annualized return, volatility, Sharpe ratio, maximum drawdown, and number of trades;
- compare a strategy against a benchmark strategy.

The current strategies include:

- `MovingAverageCrossStrategy`
- `BuyAndHoldStrategy`
- `SimpleRSIStrategy`
- `MeanReversionStrategy`

## Important backtesting assumptions

The engine avoids look-ahead bias by separating signal generation from execution:

1. The strategy receives only candles available up to the current candle.
2. A signal generated from candle `T` is based on information available at candle `T`.
3. If that signal creates an order, the order is executed at candle `T+1` open.
4. Portfolio value is recorded at each candle's close.

The default broker is long-only. A buy order uses available cash to buy as many whole shares as possible. A sell order liquidates the currently held quantity for the tested symbol. Commissions and slippage are currently ignored.

## Installation

Install the dependencies from the repository root:

```powershell
pip install -r requirements.txt
```

Because the package lives under `src`, run commands with `PYTHONPATH` pointing to `src`:

```powershell
$env:PYTHONPATH = "src"
```

On macOS or Linux:

```bash
export PYTHONPATH=src
```

## Console interface

The console interface is implemented in `src/backtester/cli.py` and can be run as a Python module:

```powershell
python -m backtester.cli backtest
```

If no command is provided, the CLI runs the `backtest` command with default parameters.

### Backtest command

`backtest` runs one strategy and prints the selected parameters followed by all metrics registered in the `PerformanceAnalyzer`.

Default parameters:

- strategy: `MovingAverageCrossStrategy(20, 50)`
- asset: `SPY`
- period length: `5` calendar years
- end date: today's date
- data source: `YFinanceDataSource`
- initial capital: `10000`

Example:

```powershell
python -m backtester.cli backtest
```

Example with custom parameters:

```powershell
python -m backtester.cli backtest --strategy moving-average --short-window 10 --long-window 40 --symbol AAPL --years 3 --initial-capital 25000
```

The output uses the format `label: result`, for example:

```text
Backtest parameters
Strategy: MovingAverageCrossStrategy(20, 50)
Asset: SPY
Period: 2021-08-19 to 2026-08-19
Years parameter: 5
Data source: YFinanceDataSource
Initial capital: 10,000.00

Performance metrics
Total return: 12.34%
Annualized return: 2.35%
Daily average return: 0.01%
Daily volatility: 1.05%
Annual volatility: 16.67%
Maximum drawdown: -18.20%
Daily Sharpe ratio: 0.0123
Annual Sharpe ratio: 0.1953
Number of trades: 4
```

### Benchmark comparison command

`compare` runs the selected strategy and a benchmark strategy on the same data. The default benchmark is `BuyAndHoldStrategy`.

The command calculates metrics for both backtests and then prints the result of `get_differences(strategy_metrics, benchmark_metrics)`. Each displayed value is:

```text
strategy metric - benchmark metric
```

Example:

```powershell
python -m backtester.cli compare --strategy moving-average --benchmark buy-and-hold --symbol SPY
```

Example output:

```text
Benchmark comparison parameters
Strategy: MovingAverageCrossStrategy(20, 50)
Benchmark: BuyAndHoldStrategy
Asset: SPY
Period: 2021-08-19 to 2026-08-19
Years parameter: 5
Data source: YFinanceDataSource
Initial capital: 10,000.00

Metric differences
Total return difference: -3.21%
Annualized return difference: -0.60%
Daily average return difference: -0.00%
Daily volatility difference: 0.15%
Annual volatility difference: 2.38%
Maximum drawdown difference: 4.10%
Daily Sharpe ratio difference: -0.0031
Annual Sharpe ratio difference: -0.0492
Number of trades difference: 3
```

## CLI options

Common options:

- `--symbol`: asset symbol, default `SPY`
- `--years`: number of calendar years to load when `--start` is omitted, default `5`
- `--start`: inclusive start date in `YYYY-MM-DD` format
- `--end`: exclusive end date in `YYYY-MM-DD` format, default is today's date
- `--source`: `yfinance` or `csv`, default `yfinance`
- `--csv-path`: CSV file or directory used with `--source csv`
- `--initial-capital`: starting cash, default `10000`

Strategy options:

- `--strategy moving-average`: uses `--short-window` and `--long-window`
- `--strategy buy-and-hold`: buys once and holds the position
- `--strategy rsi`: uses `--rsi-period`, `--rsi-min`, and `--rsi-max`
- `--strategy mean-reversion`: uses `--mean-window` and `--mean-threshold`

The `compare` command also accepts:

- `--benchmark`: `buy-and-hold`, `moving-average`, `rsi`, or `mean-reversion`, default `buy-and-hold`

## CSV data

When using CSV data, the file must contain these columns:

- `date`, `timestamp`, or `datetime`
- `open`
- `high`
- `low`
- `close`
- `volume`

Example:

```powershell
python -m backtester.cli backtest --source csv --csv-path data/SPY.csv --symbol SPY --start 2024-01-01 --end 2024-12-31
```

If `--csv-path` points to a directory, QuantReplay looks for a file named `<SYMBOL>.csv` in that directory. If the CSV contains a `symbol` column, rows are filtered to the requested symbol.

## Running tests

Run the test suite from the repository root:

```powershell
pytest
```
