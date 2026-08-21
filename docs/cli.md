# CLI reference

The console interface is implemented in `src/backtester/cli.py` and can be run
as a Python module:

```powershell
python -m backtester.cli backtest
```

If no command is provided, the CLI runs `backtest` with its default parameters.

## Backtest command

`backtest` runs one strategy and prints the selected parameters followed by all
metrics registered with `PerformanceAnalyzer`.

Default parameters:

- strategy: `MovingAverageCrossStrategy(20, 50)`;
- asset: `SPY`;
- period length: five calendar years;
- end date: today's date;
- data source: `YFinanceDataSource`;
- initial capital: `10000`;
- position sizing: `AllInAllOutSizer`.

Run with defaults:

```powershell
python -m backtester.cli backtest
```

Run with custom parameters:

```powershell
python -m backtester.cli backtest --strategy moving-average --short-window 10 --long-window 40 --symbol AAPL --years 3 --initial-capital 25000 --sizing percent --buy-percent 0.5 --sell-percent 1
```

Output uses the format `label: result`:

```text
Backtest parameters
Strategy: MovingAverageCrossStrategy(20, 50)
Asset: SPY
Period: 2021-08-19 to 2026-08-19
Years parameter: 5
Data source: YFinanceDataSource
Initial capital: 10,000.00
Position sizing: AllInAllOutSizer

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

See [Performance metrics](metrics.md) for the formulas and interpretation.

## Benchmark comparison command

`compare` runs the selected strategy and a benchmark on the same data. The
default benchmark is `BuyAndHoldStrategy`. Both runs use the selected
position-sizing configuration so that their sizing assumptions are consistent.

The command calculates metrics for both backtests and passes them to
`get_differences(strategy_metrics, benchmark_metrics)`. Each displayed value is:

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
Position sizing: AllInAllOutSizer

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

## Common options

- `--symbol`: asset symbol, default `SPY`
- `--years`: calendar years to load when `--start` is omitted, default `5`
- `--start`: inclusive start date in `YYYY-MM-DD` format
- `--end`: exclusive end date in `YYYY-MM-DD` format, default is today's date
- `--source`: `yfinance` or `csv`, default `yfinance`
- `--csv-path`: CSV file or directory used with `--source csv`
- `--initial-capital`: starting cash, default `10000`
- `--sizing`: `all-in-all-out`, `fixed`, or `percent`, default `all-in-all-out`
- `--buy-size`: positive whole-share quantity required with `--sizing fixed`
- `--sell-size`: positive whole-share quantity required with `--sizing fixed`
- `--buy-percent`: fraction of available cash from `0` to `1`, required with `--sizing percent`
- `--sell-percent`: fraction of owned shares from `0` to `1`, required with `--sizing percent`

## Strategy options

- `--strategy moving-average`: uses `--short-window` and `--long-window`
- `--strategy buy-and-hold`: buys once and holds the position
- `--strategy rsi`: uses `--rsi-period`, `--rsi-min`, and `--rsi-max`
- `--strategy mean-reversion`: uses `--mean-window` and `--mean-threshold`

The `compare` command also accepts `--benchmark`. Supported values are
`buy-and-hold`, `moving-average`, `rsi`, and `mean-reversion`; the default is
`buy-and-hold`.

For input formats and validation, see [Market data](data.md). Return to the
[project README](../README.md).
