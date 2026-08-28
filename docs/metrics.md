# Performance metrics

The CLI reports all metrics currently registered with `PerformanceAnalyzer`.

Let $V_t$ be the portfolio value at the close of observation $t$, and let
$r_t = \frac{V_t}{V_{t-1}} - 1$ be the simple return between consecutive
observations. Let $n$ be the number of those returns. Elapsed time in years is
$T = \frac{t_n - t_0}{365.25\text{ days}}$, where $t_0$ and $t_n$ are the first
and last observation timestamps. Let $\mathcal{T}$ be the set of executed
trades.

The Sharpe ratio assumes a risk-free return of zero.

The names “daily average,” “daily volatility,” and “daily Sharpe ratio” are
accurate for the daily Yahoo Finance source. The implementation actually uses
one return per pair of consecutive candles without inspecting their spacing.
For non-daily or irregular CSV input, read “daily” as “per observation.” The
annual volatility and annual Sharpe ratio still multiply by `sqrt(252)`, so
their annual interpretation is not valid for such input.

## Definitions

- Total return: $R_{total} = \frac{V_n}{V_0} - 1$
- Annualized return: $R_{annual} = \left(\frac{V_n}{V_0}\right)^{\frac{1}{T}} - 1$
- Daily average return: $\bar{r} = \frac{1}{n}\sum_{t=1}^{n} r_t$
- Daily volatility: $\sigma_d = \sqrt{\frac{1}{n-1}\sum_{t=1}^{n}\left(r_t-\bar{r}\right)^2}$
- Annual volatility: $\sigma_a = \sigma_d\sqrt{252}$
- Maximum drawdown: $MDD = \min_{0 \le t \le n}\left(\frac{V_t}{\max_{0 \le j \le t}V_j}-1\right)$
- Daily Sharpe ratio: $S_d = \frac{\bar{r}}{\sigma_d}$
- Annual Sharpe ratio: $S_a = S_d\sqrt{252}$
- Number of trades: $N_{trades} = \lvert\mathcal{T}\rvert$

## Interpretation

| Metric | Meaning | Generally good | Generally bad |
| --- | --- | --- | --- |
| Total return | Portfolio gain or loss over the whole backtest. | Higher and above the benchmark. | Negative or below the benchmark. |
| Annualized return | Total return converted to an approximate yearly growth rate. | Higher, particularly over a sufficiently long test. | Negative; short tests can also produce misleadingly large values. |
| Daily average return | Arithmetic average of period-to-period portfolio returns. | Higher when risk remains reasonable. | Negative; near zero may still be reasonable with very low risk. |
| Daily volatility | Variation in daily returns; a risk proxy rather than a return metric. | Lower for the same return. | High when returns are low or negative. |
| Annual volatility | Daily volatility scaled to a 252-trading-day year. | Lower for the same return. | High values imply larger swings. |
| Maximum drawdown | Worst peak-to-trough portfolio loss. | Closer to `0%`; for example, `-5%` is better than `-40%`. | A large negative value. |
| Daily Sharpe ratio | Average daily return per unit of daily volatility. | Higher; above zero indicates positive return relative to volatility. | Negative or near zero. |
| Annual Sharpe ratio | Daily Sharpe ratio scaled to a 252-trading-day year. | Higher; rough conventions often call above `1.0` decent and above `2.0` strong. | Below zero is poor; between zero and one may be weak. |
| Number of trades | Count of executed trades. | No universally best value. | Excessive trading increases the effect of configured costs; zero may indicate no signals or only rejected/zero-sized orders. |

These labels are only rough guidelines. Metrics should be interpreted together.
High total return is less impressive when maximum drawdown is very large, and
low volatility is not useful if a strategy earns no meaningful return.

In benchmark comparison mode, the CLI presents three value columns for every
metric shared by both runs:

| Strategy | Benchmark | Difference |
| ---: | ---: | ---: |
| Metric value from the strategy run | Metric value from the benchmark run | Strategy value minus benchmark value |

The strategy and benchmark use the same data and execution assumptions. Each
difference is calculated as:

```text
strategy metric - benchmark metric
```

A positive difference is normally good for returns and Sharpe ratios. A
negative volatility difference means the strategy fluctuated less. A positive
maximum drawdown difference is normally good because drawdown values are
negative and values closer to zero represent smaller losses. Trade-count
differences indicate only how many more or fewer successful executions the
strategy made; positive is not inherently better.

## Edge cases and limitations

- The CLI rejects data sets with fewer than two candles before calculating its
  standard metric report.
- Daily average return is defined as zero when there are no period returns.
- Daily volatility is defined as zero when fewer than two period returns exist.
- Sharpe ratios are unavailable when period volatility is zero and are printed
  as `N/A` by the CLI.
- Annual volatility and Sharpe ratio always use 252 periods per year; candle
  frequency is not inferred from timestamps.
- The Sharpe ratio uses a risk-free return of zero.
- Configured commissions reduce cash at execution. Slippage changes fill
  prices, and both therefore flow through the portfolio values used by return,
  volatility, Sharpe ratio, and drawdown calculations.
- The trade-count metric counts successful executions only. Rejected and
  zero-sized orders are not trades.
- The library-level annualized-return calculation can overflow for extreme
  growth over a very short elapsed interval.
- Library callers can construct a zero-cash, zero-position portfolio even
  though the CLI requires positive initial capital. Maximum drawdown is not
  defined safely when its first recorded portfolio value is zero.

Return to the [project README](../README.md) or see the
[CLI reference](cli.md).
