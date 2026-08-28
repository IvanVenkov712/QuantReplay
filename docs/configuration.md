# TOML configuration reference

QuantReplay can read every `backtest` and `compare` setting from a TOML file.
The command-line interface remains available for one-off overrides.

## Value priority

Effective values are selected independently with this priority:

1. an option written on the command line;
2. the corresponding option in the TOML file;
3. the default defined by the application.

For example, if `research.toml` selects `AAPL` and three years, this command
uses `MSFT` from the CLI, three years from TOML, and the default initial
capital:

```powershell
python -m backtester.cli backtest --config research.toml --symbol MSFT
```

## Configuration path

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
fall back to normal application defaults. A missing explicitly named file is
an error; this prevents a misspelled explicit path from being silently
ignored.

Relative paths, including `csv_path`, are interpreted from the current working
directory. They are not interpreted relative to the package installation or
to the custom configuration file.

The repository includes
[`quantreplay.example.toml`](../quantreplay.example.toml). Copy it to
`quantreplay.toml` to use it automatically, or pass it directly to `--config`.

## File structure

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
buffer_rate = 0.01

commission_model = "proportional"
commission_rate = 0.001
slippage_rate = 0.0005

strategy = "moving-average"
short_window = 10
long_window = 40

[compare]
benchmark = "buy-and-hold"
```

### The `[backtest]` table

`[backtest]` contains all settings shared by both commands, including the
strategy under test. Consequently, `compare` uses the same data, portfolio,
execution, and strategy settings as `backtest`.

Supported keys are:

| Group | Keys |
| --- | --- |
| Data and period | `symbol`, `years`, `start`, `end`, `source`, `csv_path` |
| Portfolio | `initial_capital` |
| Position sizing | `sizing`, `buy_size`, `sell_size`, `buy_percent`, `sell_percent`, `buffer_rate` |
| Execution costs | `commission_model`, `fixed_commission`, `commission_rate`, `slippage_rate` |
| Strategy selection | `strategy` |
| Moving average | `short_window`, `long_window` |
| RSI | `rsi_period`, `rsi_min`, `rsi_max` |
| Mean reversion | `mean_window`, `mean_threshold` |

### The `[compare]` table

`[compare]` contains only `benchmark`. It is applied by the `compare` command
and ignored by `backtest`.

The `strategy` and `benchmark` values support `buy-and-hold`,
`simple-moving-average`, `exponential-moving-average`, `cutler-rsi`,
`exponential-rsi`, `wilder-rsi`, `simple-mean-reversion`, and
`exponential-mean-reversion`. The original `moving-average`, `rsi`, and
`mean-reversion` names remain supported as aliases.

## TOML value types

Strings and dates must be quoted. Integer settings such as `years` and
`short_window` must use TOML integers. Monetary values, rates, and thresholds
accept TOML integers or floating-point numbers.

Rates are decimal fractions. For example, `0.001` means `0.1%`, not `0.001%`.

## Validation and related settings

The same semantic validation is applied regardless of where a value comes
from. Choices, positive-number constraints, rate ranges, and required related
settings are therefore identical for CLI and TOML. Unknown sections, unknown
keys, wrong TOML types, malformed TOML, and invalid combinations fail with a
clear error rather than being ignored.

Related settings must form a complete model. For example:

- `sizing = "fixed"` requires `buy_size` and `sell_size`;
- `sizing = "percent"` requires `buy_percent` and `sell_percent`;
- optional `buffer_rate` accepts `[0, 1)` and may be combined with any sizing policy;
- `commission_model = "fixed"` requires `fixed_commission`;
- `commission_model = "proportional"` requires `commission_rate`.

If a CLI option changes `sizing` or `commission_model`, TOML-only parameters
belonging to the old selection are discarded. Required parameters for the new
selection must be supplied by the CLI. This makes it possible to replace a
complete model without stale TOML settings causing a conflict:

```powershell
python -m backtester.cli backtest --config percent.toml --sizing fixed --buy-size 10 --sell-size 10
```

`buffer_rate` is independent of the base sizing selection. When present, it
caps buys to leave the configured fraction of current cash unspent, while
sells are unchanged. For example, `buffer_rate = 0.05` reserves 5% of cash.
The CLI applies it by wrapping the base `QuantityResolver` in a
`BufferQuantityResolver`. Both resolvers share one `BuyQuantityCapper`, so buy
affordability uses the same commission and slippage models as the broker.

See the [CLI reference](cli.md) for all commands and options, or return to the
[project README](../README.md).
