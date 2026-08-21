# Performance metrics

The CLI reports all metrics currently registered with `PerformanceAnalyzer`.

Let $V_t$ be the portfolio value at the close of observation $t$, and let
$r_t = \frac{V_t}{V_{t-1}} - 1$ be the simple return between consecutive
observations. Let $n$ be the number of those returns. Elapsed time in years is
$T = \frac{d_n - d_0}{365.25}$, where $d_0$ and $d_n$ are the first and last
observation dates. Let $\mathcal{T}$ be the set of executed trades.

The Sharpe ratio assumes a risk-free return of zero.

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
| Number of trades | Count of executed trades. | No universally best value. | Excessive trading is especially suspect while costs are ignored; zero may indicate no signals. |

These labels are only rough guidelines. Metrics should be interpreted together.
High total return is less impressive when maximum drawdown is very large, and
low volatility is not useful if a strategy earns no meaningful return.

In benchmark comparison mode, each difference is calculated as the strategy
metric minus the benchmark metric. A positive difference is normally good for
returns and Sharpe ratios. A negative volatility difference means the strategy
fluctuated less. A positive maximum drawdown difference is normally good
because drawdown values are negative and values closer to zero represent
smaller losses.

## Edge cases and limitations

- Daily average return is defined as zero when there are no period returns.
- Daily volatility is defined as zero when fewer than two period returns exist.
- Sharpe ratios are unavailable when daily volatility is zero.
- Annual volatility and Sharpe ratio use 252 trading periods per year.
- The Sharpe ratio uses a risk-free return of zero.
- Commissions and slippage are currently ignored, so frequently trading
  strategies may appear unrealistically favorable.

Return to the [project README](../README.md) or see the
[CLI reference](cli.md).
