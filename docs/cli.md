# CLI reference

The console interface is implemented in the `src/backtester/cli/` package. It
can be run as a Python module:

```powershell
python -m backtester.cli backtest
```

An editable installation also provides the equivalent `quantreplay` command:

```powershell
quantreplay backtest
```

If no command is provided, the CLI runs `backtest` with its default parameters.

## TOML configuration

Both commands accept a configuration path through `--config`:

```powershell
python -m backtester.cli backtest --config configs/aapl.toml
python -m backtester.cli compare --config configs/aapl.toml
```

When `--config` is omitted, QuantReplay looks for `quantreplay.toml` in the
current working directory. Values use the priority
`CLI option > TOML option > application default`.

See the dedicated [TOML configuration reference](configuration.md) for path
resolution, the complete file structure, supported keys, value types,
validation rules, and the example configuration.

## Backtest command

`backtest` runs one strategy and prints the selected parameters followed by all
metrics registered with `PerformanceAnalyzer`.

Default parameters:

- strategy selector: `moving-average`, the backward-compatible alias for
  `SimpleMovingAverageCrossStrategy(20, 50)`;
- asset: `SPY`;
- period length: five calendar years;
- end date: today's date;
- data source: `YFinanceDataSource`;
- initial capital: `10000`;
- position sizing: `all-in-all-out`;
- commission: `NoCommissionModel`;
- slippage: `ExecutionModel(rate=0.00%)`.

Run with defaults:

```powershell
python -m backtester.cli backtest
```

Run with custom parameters:

```powershell
python -m backtester.cli backtest --strategy simple-moving-average --short-window 10 --long-window 40 --symbol AAPL --years 3 --initial-capital 25000 --sizing percent --buy-percent 0.5 --sell-percent 1 --commission-model proportional --commission-rate 0.001 --slippage-rate 0.0005
```

Save the four-panel backtest dashboard to an image file:

```powershell
python -m backtester.cli backtest --symbol AAPL --chart reports/aapl-backtest.png
```

`--chart PATH` is available only for `backtest`. The image format is inferred
from the path extension, missing parent directories are created, and an
existing file is not overwritten. It can also be set as `chart = "PATH"` in
the configuration file's `[backtest]` table.

Output uses the format `label: result`. The dates and metric values below are
illustrative:

```text
Backtest parameters
Strategy: SimpleMovingAverageCrossStrategy(20, 50)
Asset: SPY
Requested period: <resolved-start-date> (inclusive) to <resolved-end-date> (exclusive)
Data used: <first-candle-date> through <last-candle-date> (<count> candles)
Data span: <elapsed-calendar-days> calendar days (<elapsed-calendar-years> years)
Years parameter: 5 (used to derive start from today's end)
Data source: YFinanceDataSource
Initial capital: 10,000.00
Position sizing: all-in-all-out
Commission: NoCommissionModel
Slippage: ExecutionModel(rate=0.00%)

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
position-sizing, commission, and slippage configuration so that their execution
assumptions are consistent.

The command calculates metrics for both backtests and displays three value
columns: the strategy result, the benchmark result, and their difference. Each
difference is:

```text
strategy metric - benchmark metric
```

Example:

```powershell
python -m backtester.cli compare --strategy simple-moving-average --benchmark buy-and-hold --symbol SPY
```

Example output:

```text
Benchmark comparison parameters
Strategy: SimpleMovingAverageCrossStrategy(20, 50)
Benchmark: BuyAndHoldStrategy
Asset: SPY
Requested period: <resolved-start-date> (inclusive) to <resolved-end-date> (exclusive)
Data used: <first-candle-date> through <last-candle-date> (<count> candles)
Data span: <elapsed-calendar-days> calendar days (<elapsed-calendar-years> years)
Years parameter: 5 (used to derive start from today's end)
Data source: YFinanceDataSource
Initial capital: 10,000.00
Position sizing: all-in-all-out
Commission: NoCommissionModel
Slippage: ExecutionModel(rate=0.00%)

Metric comparison
Metric                       Strategy  Benchmark  Difference
Total return                   16.79%      20.00%      -3.21%
Annualized return               3.16%       3.76%      -0.60%
Daily average return            0.01%       0.01%      -0.00%
Daily volatility                1.02%       0.87%       0.15%
Annual volatility              16.19%      13.81%       2.38%
Maximum drawdown              -11.90%     -16.00%       4.10%
Daily Sharpe ratio              0.0120      0.0151      -0.0031
Annual Sharpe ratio             0.1905      0.2397      -0.0492
Number of trades                     4           1            3
```

## Common options

- `--config`: TOML configuration path; default lookup is `quantreplay.toml` in
  the current working directory; see [TOML configuration](configuration.md)
- `--symbol`: asset symbol, default `SPY`
- `--years`: calendar years used to derive a missing date boundary, default `5`
- `--start`: inclusive start date in `YYYY-MM-DD` format
- `--end`: exclusive end date in `YYYY-MM-DD` format
- `--source`: `yfinance` or `csv`, default `yfinance`
- `--csv-path`: CSV file or directory used with `--source csv`
- `--csv-period-anchor`: no-date CSV behavior: `start-csv` (default),
  `end-today`, or `end-csv`
- `--initial-capital`: starting cash, default `10000`
- `--sizing`: `all-in-all-out`, `fixed`, or `percent`, default `all-in-all-out`
- `--buy-size`: positive whole-share quantity required with `--sizing fixed`
- `--sell-size`: positive whole-share quantity required with `--sizing fixed`
- `--buy-percent`: fraction of available cash from `0` to `1`, required with `--sizing percent`
- `--sell-percent`: fraction of owned shares from `0` to `1`, required with `--sizing percent`
- `--buffer-rate`: optional fraction of cash reserved from buys, from `0` inclusive to `1` exclusive; compatible with every sizing policy
- `--commission-model`: `none`, `fixed`, or `proportional`, default `none`
- `--fixed-commission`: non-negative cash amount per executed trade, required with `--commission-model fixed`
- `--commission-rate`: fraction of trade notional from `0` to `1`, required with `--commission-model proportional`
- `--slippage-rate`: adverse fill-price fraction from `0` inclusive to `1` exclusive, default `0`

The requested range is half-open: `--start` is included and `--end` is
excluded. Date boundaries are resolved consistently as follows:

| Supplied dates | Resolution |
| --- | --- |
| Neither date, Yahoo Finance | `end = today`, `start = end - years` |
| Neither date, CSV with `start-csv` | `start = first CSV candle for the selected symbol`, `end = start + years` |
| Neither date, CSV with `end-today` | `end = today`, `start = end - years` |
| Neither date, CSV with `end-csv` | `end = day after the selected symbol's last CSV candle`, `start = end - years` |
| Only `--end` | `start = end - years` |
| Only `--start` | `end = start + years` |
| Both dates | Use both; `years` is not applied |

Adding or subtracting calendar years preserves the month and day. February 29
is adjusted to February 28 when the resulting year is not a leap year.

`--csv-period-anchor` applies only to CSV runs where neither date is supplied.
If either date is explicit, the general missing-boundary rule takes priority.
The parameter report states whether the configured CSV anchor was applied.
Because the requested end is exclusive, `end-csv` sets that boundary to the
calendar day after the final CSV candle so that the final candle is included.

The report distinguishes the requested range from the first and last candles
actually returned by the data source and states how the years parameter was
applied. The displayed data span is the elapsed calendar time between those
candles, using the same 365.25-day year as the annualized-return calculation.

## Buffered quantity resolution

`--buffer-rate` caps buy orders to the whole shares affordable after reserving
the configured fraction of current cash. The CLI implements this by wrapping
the base `QuantityResolver` in `BufferQuantityResolver`; it does not alter sell
quantities.

```powershell
# Reserve 5% of cash while otherwise using all-in/all-out sizing
python -m backtester.cli backtest --buffer-rate 0.05

# The same modifier can wrap fixed or percentage sizing
python -m backtester.cli backtest --sizing percent --buy-percent 0.5 --sell-percent 1 --buffer-rate 0.02
```

The base and buffered resolvers share one `BuyQuantityCapper`. Its affordability
calculation uses the same commission and slippage models as the broker. For
fixed sizing, specifying a buffer also allows the requested quantity to be
reduced when it does not fit within the spendable cash.

## Commission and slippage

The CLI maps the commission choices to these broker models:

| CLI value | Class | Calculation |
| --- | --- | --- |
| `none` | `NoCommissionModel` | `0` |
| `fixed` | `FixedCommissionModel` | `fixed_commission` once per executed trade |
| `proportional` | `ProportionalCommissionModel` | `quantity * fill_price * commission_rate` |

Rates are decimal fractions. For example, `0.001` means `0.1%`, not `0.001%`.
The proportional rate accepts the inclusive range `[0, 1]`; the slippage rate
accepts `[0, 1)`.

Slippage always moves the fill against the trader:

```text
BUY fill  = next_open * (1 + slippage_rate)
SELL fill = next_open * (1 - slippage_rate)
```

Examples:

```powershell
# No commission and no slippage (the defaults)
python -m backtester.cli backtest

# 2.50 cash units per executed trade and 0.05% slippage
python -m backtester.cli backtest --commission-model fixed --fixed-commission 2.50 --slippage-rate 0.0005

# 0.1% of each trade's notional
python -m backtester.cli backtest --commission-model proportional --commission-rate 0.001
```

Commission-specific values are deliberately rejected with unrelated models.
For example, `--fixed-commission` may only be supplied with
`--commission-model fixed`.

Position sizing uses the next-candle open as its reference price. All-in and
percentage BUY quantities include commission and adverse slippage in their
budget checks, even without `--buffer-rate`. An unbuffered fixed BUY remains an
exact request and can be rejected when its final cost exceeds available cash.
A rejected order is recorded with an `INSUFFICIENT_FUNDS` or
`INSUFFICIENT_POSITION` execution status, but no trade is created and no
commission is charged. The CLI lists the order's submission time, side,
quantity, symbol, and the corresponding `Insufficient funds` or
`Insufficient position` reason when a run has at most 10 rejected orders. The
submission time is the next-candle-open time, not the preceding signal time.
For larger rejection counts, the CLI prints the total and omits the individual
details. Comparison runs report strategy and benchmark rejections separately.

## Strategy options

| CLI names | Relevant options |
| --- | --- |
| `buy-and-hold` | None |
| `simple-moving-average`, `exponential-moving-average` | `--short-window`, `--long-window` |
| `cutler-rsi`, `exponential-rsi`, `wilder-rsi` | `--rsi-period`, `--rsi-min`, `--rsi-max` |
| `simple-mean-reversion`, `exponential-mean-reversion` | `--mean-window`, `--mean-threshold` |

The original names `moving-average`, `rsi`, and `mean-reversion` remain aliases
for the simple moving-average, Cutler RSI, and simple mean-reversion strategies.
The `compare` command accepts every strategy name and alias through
`--benchmark`; its default is `buy-and-hold`. Strategy-specific options are
shared by the strategy and benchmark. For example, a comparison between the
simple and exponential crossover strategies uses the same short and long
windows for both.

See the [Strategy reference](strategies.md) for indicator formulas, exact
signal boundaries, parameter constraints, warm-up periods, examples, and test
coverage for every available strategy.

For input formats and validation, see [Market data](data.md). Return to the
[project README](../README.md).
