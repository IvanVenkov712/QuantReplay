# Known issues and follow-up work

## Financial and statistical behavior

- Metrics named “daily” operate on consecutive candle observations, while
  annual volatility and annual Sharpe ratio always assume 252 periods per year.
  Either restrict CSV input to daily candles or make periods per year explicit.
- Annualized return can overflow for extreme growth over a very short elapsed
  interval. Consider a log-space calculation with an explicit infinity or
  `N/A` policy.
- The library API permits a portfolio value of zero, but maximum drawdown
  divides by the running peak and is not defined safely when the first value is
  zero. The CLI avoids this state by requiring positive initial capital.

## Maintenance

- Apply complete integer and relationship validation to strategy parameters at
  the CLI parsing boundary instead of relying partly on strategy constructors.
- Review the older classes in `src/backtester/sizing/position_sizing.py`; the
  CLI and engine use the sizing-instruction and resolver path instead.
- Consider converting mutable sequences supplied to frozen `BacktestResult`
  instances into tuples so the result is deeply immutable.
