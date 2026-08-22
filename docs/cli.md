# CLI reference

The console interface is implemented in `src/backtester/cli.py` and can be run
as a Python module:

```powershell
python -m backtester.cli backtest
```

If no command is provided, the CLI runs `backtest` with its default parameters.

## TOML configuration

Every `backtest` and `compare` option can be stored in a TOML file. Effective
values are selected independently with this priority:

1. an option written on the command line;
2. the corresponding option in the TOML file;
3. the default defined by the application.

For example, if the file selects `AAPL` and three years, this command uses
`MSFT` from the CLI, three years from TOML, and the default initial capital:

```powershell
python -m backtester.cli backtest --config research.toml --symbol MSFT
```

### Configuration path

Pass a file explicitly with `--config`:

```powershell
python -m backtester.cli backtest --config configs/aapl.toml
python -m backtester.cli compare --config configs/aapl.toml
```

`--config` can also precede an explicit command:

```powershell
python -m backtester.cli --config configs/aapl.toml compare
```

When `--config` is omitted, QuantReplay looks for `quantreplay.toml` in the
current working directory. A missing default file is ignored and all values
fall back to normal CLI defaults. A missing explicitly named file is an error;
this distinction prevents a misspelled explicit path from being silently
ignored.

Relative paths, including `csv_path`, are interpreted from the current working
directory. They are not interpreted relative to the package installation or
to the custom configuration file.

The repository includes
[`quantreplay.example.toml`](../quantreplay.example.toml). Copy it to
`quantreplay.toml` to use it automatically, or pass it directly to `--config`.

### File structure

Configuration uses snake_case keys corresponding directly to kebab-case CLI
options. For example, `initial_capital` represents `--initial-capital` and
`short_window` represents `--short-window`.

```toml
[backtest]
symbol = "AAPL"
years = 3
source = "csv"
csv_path = "data/AAPL.csv"
initial_capital = 25000.0

sizing = "percent"
buy_percent = 0.5
sell_percent = 1.0

commission_model = "proportional"
commission_rate = 0.001
slippage_rate = 0.0005

strategy = "moving-average"
short_window = 10
long_window = 40

[compare]
benchmark = "buy-and-hold"
```

`[backtest]` contains all settings shared by both commands, including the
strategy under test. Consequently, `compare` uses the same data, portfolio,
execution, and strategy settings as `backtest`. `[compare]` contains only
`benchmark` and is ignored by the `backtest` command.

Supported `[backtest]` keys are:

| Group | Keys |
| --- | --- |
| Data and period | `symbol`, `years`, `start`, `end`, `source`, `csv_path` |
| Portfolio | `initial_capital` |
| Position sizing | `sizing`, `buy_size`, `sell_size`, `buy_percent`, `sell_percent` |
| Execution costs | `commission_model`, `fixed_commission`, `commission_rate`, `slippage_rate` |
| Strategy selection | `strategy` |
| Moving average | `short_window`, `long_window` |
| RSI | `rsi_period`, `rsi_min`, `rsi_max` |
| Mean reversion | `mean_window`, `mean_threshold` |

Strings and dates must be quoted. Integer settings such as `years` and
`short_window` must use TOML integers. Monetary values, rates, and thresholds
accept TOML integers or floating-point numbers. Rates remain decimal fractions:
`0.001` means `0.1%`.

The same semantic validation is applied regardless of where a value comes
from. Choices, positive-number constraints, rate ranges, and required related
settings are therefore identical for CLI and TOML. Unknown sections, unknown
keys, wrong TOML types, malformed TOML, and invalid combinations fail with a
clear error rather than being ignored.

Related settings still have to form a complete model. For example,
`sizing = "fixed"` requires both `buy_size` and `sell_size`. If a CLI option
changes `sizing` or `commission_model`, TOML-only parameters belonging to the
old selection are discarded; required parameters for the new selection must
be supplied by the CLI. This makes it possible to replace a complete model
without stale TOML settings causing a conflict:

```powershell
python -m backtester.cli backtest --config percent.toml --sizing fixed --buy-size 10 --sell-size 10
```

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
- position sizing: `AllInAllOutSizer`;
- commission: `NoCommissionModel`;
- slippage: `ExecutionModel(rate=0.00%)`.

Run with defaults:

```powershell
python -m backtester.cli backtest
```

Run with custom parameters:

```powershell
python -m backtester.cli backtest --strategy moving-average --short-window 10 --long-window 40 --symbol AAPL --years 3 --initial-capital 25000 --sizing percent --buy-percent 0.5 --sell-percent 1 --commission-model proportional --commission-rate 0.001 --slippage-rate 0.0005
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
Commission: NoCommissionModel
Slippage: ExecutionModel(rate=0.00%)

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

- `--config`: TOML configuration path; default lookup is `quantreplay.toml` in the current working directory
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
- `--commission-model`: `none`, `fixed`, or `proportional`, default `none`
- `--fixed-commission`: non-negative cash amount per executed trade, required with `--commission-model fixed`
- `--commission-rate`: fraction of trade notional from `0` to `1`, required with `--commission-model proportional`
- `--slippage-rate`: adverse fill-price fraction from `0` inclusive to `1` exclusive, default `0`

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

Position sizing uses the unadjusted next-candle open and does not reserve cash
for commission or slippage. Consequently, an order—especially an
`all-in-all-out` BUY—can be rejected when its final cost exceeds available
cash. A rejected order is recorded as unsuccessful, but no trade is created and
no commission is charged.

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
