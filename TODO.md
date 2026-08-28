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

The main CLI path is healthy: I found no critical bug or look-ahead bias. Next-candle-open execution, cost-aware sizing, broker accounting, and close-time valuation are correctly sequenced.

## Findings

1. **Medium – Non-daily CSV metrics can be materially misleading.**  
   CSV accepts intraday and irregular candles, but “daily” volatility and Sharpe calculations treat every adjacent observation as one day and always annualize with `sqrt(252)`. This is documented, but still permits financially incorrect-looking output for supported input. Make `periods_per_year` explicit, infer/validate frequency, or restrict the CLI to daily data. See [metrics.py](/C:/Users/ivanv/FMI/QuantReplay/src/backtester/metrics/metrics.py:120) and [loader.py](/C:/Users/ivanv/FMI/QuantReplay/src/backtester/data/loader.py:136).

2. **Medium – Maximum drawdown crashes when the initial portfolio value is zero.**  
   `Portfolio` permits zero cash, while `max_drawdown()` divides by a zero running peak. The CLI prevents this, but the library API does not. This is already acknowledged in TODO. See [metrics.py](/C:/Users/ivanv/FMI/QuantReplay/src/backtester/metrics/metrics.py:142) and [portfolio.py](/C:/Users/ivanv/FMI/QuantReplay/src/backtester/portfolio/portfolio.py:77).

3. **Medium – Invalid strategy output is silently treated like HOLD.**  
   If a custom strategy accidentally returns `None`, `"buy"`, or another invalid object, the engine produces no order and stores the invalid value in `BacktestRecord`. It should fail immediately unless the result is a `Signal`. See [backtest.py](/C:/Users/ivanv/FMI/QuantReplay/src/backtester/engine/backtest.py:89) and [backtest.py](/C:/Users/ivanv/FMI/QuantReplay/src/backtester/engine/backtest.py:126).

4. **Medium – Reusing stateful dependencies can contaminate backtests.**  
   The engine never resets its strategy, and its result includes the broker’s entire trade history. Reusing a `BuyAndHoldStrategy` can suppress the second run’s buy; reusing a broker can include trades from earlier runs. Decide whether the engine owns lifecycle—reset/snapshot automatically—or require fresh dependencies and document that contract. See [backtest.py](/C:/Users/ivanv/FMI/QuantReplay/src/backtester/engine/backtest.py:63) and [backtest.py](/C:/Users/ivanv/FMI/QuantReplay/src/backtester/engine/backtest.py:94).

5. **Low – “Immutable” backtest results remain mutable.**  
   `BacktestResult` is frozen, but contains mutable lists. A caller can alter a cached result’s records, orders, or trades. Convert these sequences to tuples in `__post_init__` or when constructing the result. This is also in TODO. See [backtest_result.py](/C:/Users/ivanv/FMI/QuantReplay/src/backtester/engine/backtest_result.py:28).

6. **Low – Fixed commission does not reject `NaN` or infinity at construction.**  
   These values pass `commission < 0` and cause a later execution-time failure. Validate type and finiteness consistently with the other financial models. See [costs.py](/C:/Users/ivanv/FMI/QuantReplay/src/backtester/execution/costs.py:50).

7. **Architectural cleanup is needed around obsolete implementations.**

   - [position_sizing.py](/C:/Users/ivanv/FMI/QuantReplay/src/backtester/sizing/position_sizing.py:1) is a fully tested but unused sizing system; the runtime uses `SizingInstruction`, `SizingPlan`, and resolvers instead.
   - [_MovingAverageCrossStrategy](/C:/Users/ivanv/FMI/QuantReplay/src/backtester/strategies/moving_average.py:71) and [_MeanReversionStrategy](/C:/Users/ivanv/FMI/QuantReplay/src/backtester/strategies/mrma.py:51) duplicate the active implementations.
   - [rsi_strategies.py](/C:/Users/ivanv/FMI/QuantReplay/src/backtester/strategies/rsi_strategies.py:12) contains a large obsolete commented implementation.
   - [breakout.py](/C:/Users/ivanv/FMI/QuantReplay/src/backtester/strategies/breakout.py) and the `reporting` package are empty placeholders.
   - `SizingMode.UP_TO`, `ResolutionContext.portfolio_value`, and `estimate_sell_cost()` currently have no production consumer.

8. **Backtest records are too thin for auditing and future visualization.**  
   Each record stores cash and total equity but not quantity, position market value, or positions. Executed orders also discard the originating intent’s timestamp, and zero-sized intents disappear entirely. The current single-symbol results can be reconstructed, but explicit snapshots would better expose portfolio accounting and signal-to-fill timing. See [backtest_result.py](/C:/Users/ivanv/FMI/QuantReplay/src/backtester/engine/backtest_result.py:19).

9. **The data-download helper performs destructive work on import.**  
   Importing [data_download.py](/C:/Users/ivanv/FMI/QuantReplay/data_download.py:1) immediately makes three network requests and overwrites tracked CSV files using hard-coded symbols and dates. It should use functions, a `main` guard, arguments, and explicit output paths.

10. **Quality tooling has small gaps.**  
    CI installs `flake8` separately, but it is absent from the documented `dev` extra; style lint uses `--exit-zero`, and coverage has no minimum threshold. Consequently, the local development installation cannot reproduce every CI command and gradual quality regressions do not fail CI. See [pyproject.toml](/C:/Users/ivanv/FMI/QuantReplay/pyproject.toml:29) and [python-package.yml](/C:/Users/ivanv/FMI/QuantReplay/.github/workflows/python-package.yml:28).

## Existing unfinished work

The items in [TODO.md](/C:/Users/ivanv/FMI/QuantReplay/TODO.md:1) are still accurate: frequency-aware metrics, annualized-return overflow, zero-value drawdown, complete CLI strategy validation, duplicate sizing review, and deep result immutability.

## Verification

- 390 tests passed.
- Statement coverage: 90%.
- Installed dependencies are consistent.
- CSV backtest and comparison smoke tests succeeded.
- Worktree remained clean; no files were modified.