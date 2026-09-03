# Strategy reference

Strat Echo exposes eight concrete strategies through the CLI. Their signal
rules are tested directly or through their shared strategy family, indicator
calculator, CLI wiring, and end-to-end backtest tests. Tests establish the
implemented behavior; they do not establish that a strategy is profitable or
appropriate for live trading.

## Available strategies

| CLI name | Implementation | Parameters | First possible signal |
| --- | --- | --- | --- |
| `buy-and-hold` | `BuyAndHoldStrategy` | None | First candle close |
| `simple-moving-average` | `SimpleMovingAverageCrossStrategy` | `short_window`, `long_window` | Close number `long_window + 1` |
| `exponential-moving-average` | `ExponentialMovingAverageCrossStrategy` | `short_window`, `long_window` | Close number `long_window + 1` |
| `cutler-rsi` | `CutlerRSIStrategy` | `rsi_period`, `rsi_min`, `rsi_max` | Close number `rsi_period + 1` |
| `exponential-rsi` | `ExponentialRSIStrategy` | `rsi_period`, `rsi_min`, `rsi_max` | Close number `rsi_period + 1` |
| `wilder-rsi` | `WilderRSIStrategy` | `rsi_period`, `rsi_min`, `rsi_max` | Close number `rsi_period + 1` |
| `simple-mean-reversion` | `SimpleMeanReversionStrategy` | `mean_window`, `mean_threshold` | Close number `mean_window` |
| `exponential-mean-reversion` | `ExponentialMeanReversionStrategy` | `mean_window`, `mean_threshold` | Close number `mean_window` |

The original CLI names remain supported as aliases:

| Alias | Equivalent strategy |
| --- | --- |
| `moving-average` | `simple-moving-average` |
| `rsi` | `cutler-rsi` |
| `mean-reversion` | `simple-mean-reversion` |

Every canonical name and alias may be used with `--strategy` or `--benchmark`.
The default selector is the `moving-average` alias, which creates
`SimpleMovingAverageCrossStrategy(20, 50)`.

## Shared signal and execution timing

All strategies process candles chronologically through `on_candle`. Although
each call receives a complete `Candle`, the current implementations use only
its close for indicator calculations; buy-and-hold ignores its price fields.
The strategies do not read future candles, portfolio balance, or position.

For candle `T`, the engine follows this sequence:

1. Execute any intent produced after candle `T-1`, using candle `T`'s open.
2. Pass candle `T` to the strategy and calculate a signal from information
   available through its close.
3. Store a BUY or SELL signal as an unsized order intent timestamped at candle
   `T`.
4. Value the portfolio using candle `T`'s close.
5. Resolve and execute that intent no earlier than candle `T+1`'s open. The
   resulting order retains candle `T` as its `signal_timestamp` and records
   candle `T+1` as its `submitted_timestamp`.

This means a signal calculated from a close never executes at that same
close. A signal on the final candle cannot execute because no next candle is
available. Warm-up signals are HOLD. A strategy's `reset` method clears its
indicator and signal state, although a normal CLI run creates a fresh strategy
and runs its engine only once.

Strategies express desired actions without inspecting holdings. Repeated BUY
or SELL signals are therefore possible. The sizing and resolution components
may convert such a signal to no order when its resolved whole-share quantity
is zero, and the broker may reject an unaffordable fixed-size order.

## Indicator conventions

Let `C_t` be the close at period `t` and let `n` be a window size.

### Simple moving average

The simple moving average uses the latest `n` closes, including the current
close:

$$
SMA_t(n) = \frac{1}{n}\sum_{i=0}^{n-1} C_{t-i}
$$

It is unavailable until `n` closes have been observed.

### Exponential moving average

An exponential moving average is seeded with the simple average of its first
`n` values. Each later value is:

$$
EMA_t = \alpha x_t + (1 - \alpha)EMA_{t-1}
$$

The standard exponential variants use `alpha = 2 / (n + 1)`. Wilder RSI uses
Wilder's `alpha = 1 / n`. These exponential factories require `n > 1`.

### Relative strength index

For consecutive closes, the RSI calculator separates each change into an
upward and downward move:

$$
\Delta_t = C_t - C_{t-1}, \quad
U_t = \max(\Delta_t, 0), \quad
D_t = \max(-\Delta_t, 0)
$$

After averaging gains and losses separately, it calculates:

$$
RS = \frac{A_U}{A_D}, \qquad
RSI = 100 - \frac{100}{1 + RS}
$$

If average loss is zero, RSI is `100`; if both average gain and average loss
are zero, RSI is `50`. A period of `n` requires one initial close plus `n`
price changes, so the first RSI is available after `n + 1` closes.

## Buy and hold

`BuyAndHoldStrategy` emits BUY on its first candle and HOLD thereafter. Under
the shared timing model, that first BUY executes at the second candle's open.
It never emits SELL, so any acquired position remains open through the end of
the backtest and is valued at each close.

```powershell
python -m backtester.cli backtest --strategy buy-and-hold
```

## Moving-average crossover strategies

Both crossover strategies maintain a short and a long average of closes.
They require positive windows with `short_window < long_window`. The simple
variant accepts a window of one; the exponential variant requires both windows
to be greater than one.

The first pair of complete averages establishes a baseline and produces HOLD.
For later candles:

| Previous relationship | Current relationship | Signal |
| --- | --- | --- |
| Short at or below long | Short strictly above long | BUY |
| Short at or above long | Short strictly below long | SELL |
| Any other transition | — | HOLD |

Equality alone does not produce a trade. The strategy signals only on a
crossover, rather than on every candle that remains above or below.

`simple-moving-average` uses simple moving averages:

```powershell
python -m backtester.cli backtest --strategy simple-moving-average --short-window 20 --long-window 50
```

`exponential-moving-average` uses standard exponential moving averages:

```powershell
python -m backtester.cli backtest --strategy exponential-moving-average --short-window 20 --long-window 50
```

## RSI strategies

All RSI variants use the same threshold rule:

| RSI value | Signal |
| --- | --- |
| Strictly below `rsi_min` | BUY |
| Strictly above `rsi_max` | SELL |
| Equal to either threshold, or between them | HOLD |

The constraints are `rsi_period > 1` and
`0 <= rsi_min <= rsi_max <= 100`. These are level-based signals, not threshold
crossings, so RSI can emit the same action on consecutive candles.

The variants differ only in how average gains and losses are calculated:

- `cutler-rsi` uses simple moving averages over the latest `rsi_period`
  changes.
- `exponential-rsi` uses exponential averages with
  `alpha = 2 / (rsi_period + 1)`.
- `wilder-rsi` uses Wilder averages with `alpha = 1 / rsi_period`.

```powershell
python -m backtester.cli backtest --strategy cutler-rsi --rsi-period 14 --rsi-min 30 --rsi-max 70
python -m backtester.cli backtest --strategy exponential-rsi --rsi-period 14 --rsi-min 30 --rsi-max 70
python -m backtester.cli backtest --strategy wilder-rsi --rsi-period 14 --rsi-min 30 --rsi-max 70
```

## Mean-reversion strategies

The mean-reversion strategies compare the current close with an average that
already includes that close. Let `A_t` be the selected moving average and let
`q` be `mean_threshold`:

| Current close | Signal |
| --- | --- |
| `C_t < q * A_t` | BUY |
| `C_t >= A_t` | SELL |
| `q * A_t <= C_t < A_t` | HOLD |

The window must be positive, the exponential variant requires a window greater
than one, and `mean_threshold` must be in `[0, 1]`. Like RSI, these are
level-based rules and may repeat on consecutive candles.

`simple-mean-reversion` uses a simple moving average:

```powershell
python -m backtester.cli backtest --strategy simple-mean-reversion --mean-window 20 --mean-threshold 0.95
```

`exponential-mean-reversion` uses a standard exponential moving average:

```powershell
python -m backtester.cli backtest --strategy exponential-mean-reversion --mean-window 20 --mean-threshold 0.95
```

## Strategy parameters in comparisons

The `compare` command uses one shared set of strategy parameters. For example,
`--short-window` and `--long-window` configure whichever selected strategy or
benchmark uses moving averages. If both sides belong to the same family, both
receive the same values; there are no separate benchmark window or threshold
options.

```powershell
python -m backtester.cli compare --strategy simple-moving-average --benchmark exponential-moving-average --short-window 20 --long-window 50
```

Both runs also share the symbol, candles, initial capital, cash buffer,
commission model, and slippage model. The selected sizing plan applies only to
the strategy; the benchmark uses all-in/all-out. See the [CLI reference](cli.md)
for those options and [Market data](data.md) for input conventions.

## Test coverage

The strategy behavior is checked in layers:

- [`test_moving_average_strategies.py`](../tests/test_moving_average_strategies.py)
  checks crossover validation, signal boundaries, close-price input, warm-up,
  and reset behavior.
- [`test_rsi_strategies.py`](../tests/test_rsi_strategies.py) checks threshold
  boundaries, parameter validation, close-price input, warm-up, and reset.
- [`test_mean_reversion_strategies.py`](../tests/test_mean_reversion_strategies.py)
  checks threshold boundaries, validation, close-price input, warm-up, and
  reset.
- [`test_moving_average_calculators.py`](../tests/test_moving_average_calculators.py)
  and [`test_rsi_calculators.py`](../tests/test_rsi_calculators.py) check the
  simple, standard exponential, Wilder, and RSI calculations.
- [`test_cli.py`](../tests/test_cli.py) checks every concrete strategy name,
  legacy alias, constructor mapping, printed description, and a buy-and-hold
  run through the CLI.
- [`test_backtest.py`](../tests/test_backtest.py) checks chronological candle
  delivery and next-candle-open execution independently from any specific
  strategy implementation.

Return to the [project README](../README.md).
