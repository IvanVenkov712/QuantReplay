from datetime import datetime, timedelta
from math import isclose, sqrt

import pytest

from backtester.engine.backtest_result import BacktestRecord, BacktestResult
from backtester.metrics.metrics import (
    MetricData,
    PerformanceAnalyzer,
    annual_sharpe_ratio,
    annual_volatility,
    annualized_return,
    daily_avg,
    daily_sharpe_ratio,
    daily_volatility,
    max_drawdown,
    number_of_trades,
    period_returns,
    total_return,
)
from backtester.portfolio.trade import Side, Trade
from backtester.strategies.base import Signal


def make_result(
    values: list[float],
    *,
    start: datetime = datetime(2026, 1, 1),
    trades: list[Trade] | None = None,
) -> BacktestResult:
    records = [
        BacktestRecord(
            timestamp=start + timedelta(days=index),
            generated_signal=Signal.HOLD,
            portfolio_value_at_close=value,
            cash=value,
        )
        for index, value in enumerate(values)
    ]

    return BacktestResult(records=records, trades=trades or [], orders=[])


def test_total_return_uses_first_and_last_portfolio_values() -> None:
    result = make_result([1_000, 1_100, 1_250])

    assert total_return(result) == 0.25


def test_annualized_return_uses_elapsed_calendar_days() -> None:
    result = make_result(
        [100, 121],
        start=datetime(2026, 1, 1),
    )
    result = BacktestResult(
        records=[
            result.records[0],
            BacktestRecord(
                timestamp=datetime(2027, 1, 1),
                generated_signal=Signal.HOLD,
                portfolio_value_at_close=121,
                cash=121,
            ),
        ],
        trades=[],
        orders=[],
    )

    expected = (121 / 100) ** (365.25 / 365) - 1

    assert isclose(annualized_return(result), expected)


def test_period_returns_are_simple_returns_between_consecutive_records() -> None:
    result = make_result([100, 120, 108])

    assert period_returns(result) == pytest.approx([0.2, -0.1])


def test_daily_average_is_mean_of_period_returns() -> None:
    result = make_result([100, 120, 108])

    assert daily_avg(result) == pytest.approx(0.05)


def test_daily_average_is_zero_when_no_period_returns_exist() -> None:
    result = make_result([100])

    assert daily_avg(result) == 0


def test_daily_volatility_uses_sample_standard_deviation() -> None:
    result = make_result([100, 120, 108])

    assert daily_volatility(result) == pytest.approx(sqrt(0.045))


def test_daily_volatility_is_zero_with_fewer_than_two_period_returns() -> None:
    result = make_result([100, 110])

    assert daily_volatility(result) == 0


def test_annual_volatility_scales_daily_volatility_by_trading_days() -> None:
    result = make_result([100, 120, 108])

    assert annual_volatility(result) == pytest.approx(sqrt(0.045) * sqrt(252))


def test_max_drawdown_returns_largest_peak_to_trough_loss() -> None:
    result = make_result([100, 120, 90, 135, 108])

    assert max_drawdown(result) == pytest.approx(-0.25)


def test_max_drawdown_is_zero_when_portfolio_never_falls_below_peak() -> None:
    result = make_result([100, 110, 120])

    assert max_drawdown(result) == 0


def test_sharpe_ratios_use_average_return_divided_by_volatility() -> None:
    result = make_result([100, 120, 108])
    expected_daily_sharpe = 0.05 / sqrt(0.045)

    assert daily_sharpe_ratio(result) == pytest.approx(expected_daily_sharpe)
    assert annual_sharpe_ratio(result) == pytest.approx(
        expected_daily_sharpe * sqrt(252)
    )


def test_number_of_trades_counts_recorded_trades() -> None:
    trades = [
        Trade("AAPL", Side.BUY, quantity=10, price=20, timestamp=datetime(2026, 1, 2)),
        Trade("AAPL", Side.SELL, quantity=4, price=25, timestamp=datetime(2026, 1, 3)),
    ]
    result = make_result([1_000], trades=trades)

    assert number_of_trades(result) == 2


def test_performance_analyzer_calculates_registered_metrics() -> None:
    result = make_result([100, 125])
    analyzer = PerformanceAnalyzer()
    analyzer.add_metric_func("total_return", "Total return", total_return)
    analyzer.add_metric_func("trades", "Number of trades", number_of_trades)

    assert analyzer.calculate_metrics(result) == {
        "total_return": MetricData("Total return", 0.25),
        "trades": MetricData("Number of trades", 0),
    }


def test_performance_analyzer_rejects_duplicate_metric_names() -> None:
    analyzer = PerformanceAnalyzer()
    analyzer.add_metric_func("total_return", "Total return", total_return)

    with pytest.raises(ValueError, match="metric name must be unique"):
        analyzer.add_metric_func("total_return", "Duplicate", total_return)
