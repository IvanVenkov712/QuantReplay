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
- choose all-in/all-out, fixed-share, or percentage-based position sizing;
- execute generated orders on the next candle's open;
- track cash, positions, trades, orders, and portfolio value;
- calculate performance metrics such as total return, annualized return, volatility, Sharpe ratio, maximum drawdown, and number of trades;
- compare a strategy against a benchmark strategy.

The current strategies include:

- `MovingAverageCrossStrategy`
- `BuyAndHoldStrategy`
- `SimpleRSIStrategy`
- `MeanReversionStrategy`

## Strategies and metrics

The CLI tests exactly one selected strategy at a time. With `backtest`, the selected strategy is evaluated on its own. With `compare`, the selected strategy is evaluated against a benchmark strategy on the same symbol, date range, data source, and initial capital.

By default:

- `backtest` tests `MovingAverageCrossStrategy(20, 50)`.
- `compare` tests `MovingAverageCrossStrategy(20, 50)` against `BuyAndHoldStrategy`.
- Both commands use `AllInAllOutSizer`.

Available strategies:

| CLI name | Class | What it tests | Buy signal | Sell signal |
| --- | --- | --- | --- | --- |
| `moving-average` | `MovingAverageCrossStrategy` | A trend-following idea: a short moving average crossing above or below a long moving average may indicate a change in trend. | The short average crosses above the long average. | The short average crosses below the long average. |
| `buy-and-hold` | `BuyAndHoldStrategy` | A passive benchmark: buy once at the beginning and hold until the end. | The first time the strategy is called. | Never. |
| `rsi` | `SimpleRSIStrategy` | A momentum/mean-reversion indicator based on recent average gains and losses. | RSI falls below the minimum threshold, default `30`. | RSI rises above the maximum threshold, default `70`. |
| `mean-reversion` | `MeanReversionStrategy` | A mean-reversion idea: unusually low prices may move back toward their recent average. | Current close is below `average * threshold`. | Current close is at or above the average. |

The available benchmark strategies are the same four strategies. `BuyAndHoldStrategy` is the default benchmark because it answers a simple question: did the active strategy add value compared with just buying the asset and holding it?

### Position sizing

Position sizing converts a buy or sell signal into a whole-share order quantity. The CLI supports three policies:

| CLI name | Class | Buy quantity | Sell quantity |
| --- | --- | --- | --- |
| `all-in-all-out` | `AllInAllOutSizer` | Maximum whole shares affordable with the available cash at the execution open. | The entire position immediately before execution. |
| `fixed` | `FixedSizer` | The `--buy-size` number of shares. | The `--sell-size` number of shares. |
| `percent` | `PercentSizer` | Whole shares affordable with `--buy-percent` of the available cash. | `--sell-percent` of the current shares, rounded down. |

`all-in-all-out` is the default. Fixed sizing requires both `--buy-size` and `--sell-size`. Percentage sizing requires both `--buy-percent` and `--sell-percent`; each value is a fraction from `0` to `1`, so `0.25` means 25%.

Percentage sizing acts on available cash for buys and currently owned shares for sells. It does not target a percentage of total portfolio value. Because only whole shares are supported, a valid percentage can produce a quantity of zero.

Sizing occurs immediately before execution at the next candle's open. The sizing context therefore uses the portfolio state at that time and the same opening price that the broker uses to fill the order.

### Metrics

The CLI registers all metrics currently available through `PerformanceAnalyzer`:

Let $V_t$ be the portfolio value at the close of observation $t$, let $r_t = \frac{V_t}{V_{t-1}} - 1$ be the simple return between consecutive observations, and let $n$ be the number of such returns. The elapsed time in years is $T = \frac{d_n - d_0}{365.25}$, where $d_0$ and $d_n$ are the first and last observation dates. Let $\mathcal{T}$ be the set of executed trades. The Sharpe ratio assumes a risk-free return of zero.

Formulas used in this project:

- Total return: $R_{total} = \frac{V_n}{V_0} - 1$
- Annualized return: $R_{annual} = \left(\frac{V_n}{V_0}\right)^{\frac{1}{T}} - 1$
- Daily average return: $\bar{r} = \frac{1}{n}\sum_{t=1}^{n} r_t$
- Daily volatility: $\sigma_d = \sqrt{\frac{1}{n-1}\sum_{t=1}^{n}\left(r_t-\bar{r}\right)^2}$
- Annual volatility: $\sigma_a = \sigma_d\sqrt{252}$
- Maximum drawdown: $MDD = \min_{0 \le t \le n}\left(\frac{V_t}{\max_{0 \le j \le t}V_j}-1\right)$
- Daily Sharpe ratio: $S_d = \frac{\bar{r}}{\sigma_d}$
- Annual Sharpe ratio: $S_a = S_d\sqrt{252}$
- Number of trades: $N_{trades} = \lvert\mathcal{T}\rvert$

| Metric | Meaning | Generally good | Generally bad |
| --- | --- | --- | --- |
| Total return | The total portfolio gain or loss over the whole backtest. | Higher is better. Positive return means the portfolio ended above its starting value. | Negative return means the portfolio lost money. A return below the benchmark means the strategy did not justify its extra trading. |
| Annualized return | The total return converted into an approximate yearly growth rate. | Higher is better, especially when it is above the benchmark and above a reasonable passive alternative. | Negative is bad. A high value from a very short test period can be misleading. |
| Daily average return | The arithmetic average of the period-to-period portfolio returns. | Higher is better, but only when risk is also reasonable. | Negative means the average period lost money. Near zero may still be acceptable if volatility and drawdown are very low. |
| Daily volatility | How much daily returns fluctuate. It is a risk proxy, not a return metric. | Lower is usually better for the same return. A strategy with high return and controlled volatility is attractive. | High volatility means unstable returns. It is especially bad when return is low or negative. |
| Annual volatility | Daily volatility scaled to a trading-year estimate. | Lower is usually better for the same return. Useful for comparing strategies on a yearly risk scale. | High annual volatility means the strategy may be hard to hold through large swings. |
| Maximum drawdown | The worst peak-to-trough portfolio loss during the test. | Closer to `0%` is better. For example, `-5%` is much safer than `-40%`. | Large negative values are bad because they show deep losses from a prior high. |
| Daily Sharpe ratio | Average daily return per unit of daily volatility. | Higher is better. Above `0` means return was positive relative to volatility. | Negative is bad. Near zero means the strategy was not compensated much for risk. |
| Annual Sharpe ratio | Daily Sharpe ratio converted to an annual scale. | Higher is better. As a rough guide, above `1.0` is often considered decent, above `2.0` strong, and above `3.0` exceptional. | Below `0` is poor. Between `0` and `1` may be weak unless the strategy has other advantages. |
| Number of trades | How many executed trades the backtest produced. | There is no universal best value. Fewer trades can mean lower costs and simpler behavior. More trades can be fine if they improve risk-adjusted return. | Too many trades can be bad because this project currently ignores commissions and slippage, so very active strategies may look better than they would in reality. Zero trades may mean the strategy never found a signal. |

When there are no period returns, the daily average return is defined as zero. Daily volatility is defined as zero when fewer than two period returns are available, and the Sharpe ratios are reported as unavailable when daily volatility is zero.

These good/bad labels are only rough guidelines. A metric should usually be read together with the others. For example, high total return is less impressive if maximum drawdown is very large, and low volatility is not useful if the strategy never earns a meaningful return. In benchmark comparison mode, a positive difference is good for return and Sharpe metrics. A negative difference is usually better for volatility because it means the tested strategy fluctuated less than the benchmark. For maximum drawdown, a positive difference is usually better because drawdown values are negative and a value closer to `0%` means a smaller peak-to-trough loss.

## Important backtesting assumptions

The engine avoids look-ahead bias by separating signal generation from execution:

1. The strategy receives only candles available up to the current candle.
2. A signal generated from candle `T` is based on information available at candle `T`.
3. The signal creates an order intent without choosing a quantity.
4. At candle `T+1` open, position size is calculated from the current portfolio and opening price. If the size is positive, the order is executed at that same opening price.
5. Portfolio value is recorded at each candle's close.

The broker is long-only. Because all-in and percentage-based buys are sized from the execution open, overnight price gaps are reflected before their quantities are chosen. Fixed-size orders can still be rejected when there is insufficient cash or an insufficient position. Commissions and slippage are currently ignored.

## Data sources and formats

QuantReplay obtains historical OHLCV candles from one of two sources. Both sources are converted to the same internal `Candle` representation before a backtest starts, so the engine does not depend directly on Yahoo Finance or on a particular CSV file.

### Yahoo Finance

`YFinanceDataSource` downloads daily (`1d`) data through the `yfinance` package. OHLC prices are requested without automatic adjustment (`auto_adjust=False`). The requested start date is inclusive and the end date is exclusive.

Example:

```powershell
python -m backtester.cli backtest --source yfinance --symbol SPY --start 2024-01-01 --end 2025-01-01
```

The downloaded column names are normalized and the data then passes through the same validation as CSV input.

### CSV files

Use `--source csv` together with `--csv-path`. The path may identify a single file or a directory. For a directory, QuantReplay looks for `<SYMBOL>.csv`; for example, the symbol `SPY` maps to `SPY.csv`.

A CSV file must contain one timestamp column named `date`, `timestamp`, or `datetime`, plus all five OHLCV columns:

| Column | Required | Meaning |
| --- | --- | --- |
| `date`, `timestamp`, or `datetime` | One of these is required | Candle timestamp in a format understood by pandas |
| `open` | Yes | Opening price |
| `high` | Yes | Highest price |
| `low` | Yes | Lowest price |
| `close` | Yes | Closing price |
| `volume` | Yes | Traded volume |
| `symbol` | No | Allows one file to contain multiple symbols; matching rows are selected |

Column names are converted to lowercase and spaces are replaced with underscores. If a `symbol` column is present, matching is case-sensitive.

Example CSV:

```csv
date,symbol,open,high,low,close,volume
2024-01-02,SPY,472.16,473.67,470.49,472.65,12345678
2024-01-03,SPY,470.43,471.19,468.17,468.79,14567890
```

Example command:

```powershell
python -m backtester.cli backtest --source csv --csv-path data/SPY.csv --symbol SPY --start 2024-01-01 --end 2025-01-01
```

### Validation and normalization

Before data reaches the engine, QuantReplay requires:

- timestamps sorted in ascending order with no duplicates;
- numeric, finite, and non-missing OHLCV values;
- strictly positive `open`, `high`, `low`, and `close` prices;
- non-negative volume;
- `high` greater than or equal to `low`;
- `open` and `close` between `low` and `high`.

Rows outside the requested date range are removed. QuantReplay does not sort rows, fill missing values, remove duplicate timestamps, resample candles, or otherwise repair invalid market data automatically. Invalid input fails with a clear error so that changes to financial data remain explicit.

## Installation

Install QuantReplay from the repository root in editable mode:

```powershell
python -m pip install -e .
```

This installs the package and its runtime dependencies (`pandas`,
`typing-extensions`, and `yfinance`). Editable mode means changes made under
`src` are immediately available without reinstalling the package.

For development, install the optional `dev` dependency group as well:

```powershell
python -m pip install -e ".[dev]"
```

The `.[dev]` form installs the same package and runtime dependencies, plus
development tools such as `pytest` and `pytest-cov`. The quotes prevent shells
from interpreting the square brackets. Because both commands install the
package itself, you do not need to set `PYTHONPATH` manually.

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
- position sizing: `AllInAllOutSizer`

Example:

```powershell
python -m backtester.cli backtest
```

Example with custom parameters:

```powershell
python -m backtester.cli backtest --strategy moving-average --short-window 10 --long-window 40 --symbol AAPL --years 3 --initial-capital 25000 --sizing percent --buy-percent 0.5 --sell-percent 1
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

### Benchmark comparison command

`compare` runs the selected strategy and a benchmark strategy on the same data. The default benchmark is `BuyAndHoldStrategy`. Both runs use the selected position-sizing configuration so that their sizing assumptions are consistent.

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

## CLI options

Common options:

- `--symbol`: asset symbol, default `SPY`
- `--years`: number of calendar years to load when `--start` is omitted, default `5`
- `--start`: inclusive start date in `YYYY-MM-DD` format
- `--end`: exclusive end date in `YYYY-MM-DD` format, default is today's date
- `--source`: `yfinance` or `csv`, default `yfinance`
- `--csv-path`: CSV file or directory used with `--source csv`
- `--initial-capital`: starting cash, default `10000`
- `--sizing`: `all-in-all-out`, `fixed`, or `percent`, default `all-in-all-out`
- `--buy-size`: positive whole-share buy quantity required with `--sizing fixed`
- `--sell-size`: positive whole-share sell quantity required with `--sizing fixed`
- `--buy-percent`: fraction of available cash from `0` to `1`, required with `--sizing percent`
- `--sell-percent`: fraction of owned shares from `0` to `1`, required with `--sizing percent`

Strategy options:

- `--strategy moving-average`: uses `--short-window` and `--long-window`
- `--strategy buy-and-hold`: buys once and holds the position
- `--strategy rsi`: uses `--rsi-period`, `--rsi-min`, and `--rsi-max`
- `--strategy mean-reversion`: uses `--mean-window` and `--mean-threshold`

The `compare` command also accepts:

- `--benchmark`: `buy-and-hold`, `moving-average`, `rsi`, or `mean-reversion`, default `buy-and-hold`

## Running tests

Run the test suite from the repository root:

```powershell
pytest
```
