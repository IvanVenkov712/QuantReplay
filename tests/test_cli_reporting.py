from datetime import datetime
from io import StringIO

import pytest

from backtester.cli.arguments import parse_args
from backtester.cli.reporting import (
    MAX_REJECTED_ORDER_DETAILS,
    describe_strategy,
    format_metric_value,
    print_metric_comparison,
    print_rejected_orders,
)
from backtester.domain.trading import (
    Order,
    OrderExecutionResult,
    OrderExecutionStatus,
    Side,
)
from backtester.engine.backtest_result import BacktestResult
from backtester.metrics.benchmark_comparison import get_differences
from backtester.metrics.metrics import MetricData

@pytest.mark.parametrize(
    ("arguments", "expected"),
    [
        (
            ["--short-window", "10", "--long-window", "40"],
            "SimpleMovingAverageCrossStrategy(10, 40)",
        ),
        (
            ["--strategy", "simple-moving-average"],
            "SimpleMovingAverageCrossStrategy(20, 50)",
        ),
        (
            ["--strategy", "exponential-moving-average"],
            "ExponentialMovingAverageCrossStrategy(20, 50)",
        ),
        (["--strategy", "buy-and-hold"], "BuyAndHoldStrategy"),
        (
            [
                "--strategy",
                "rsi",
                "--rsi-period",
                "10",
                "--rsi-min",
                "25",
                "--rsi-max",
                "75",
            ],
            "CutlerRSIStrategy(period=10, min=25.0, max=75.0)",
        ),
        (
            ["--strategy", "cutler-rsi"],
            "CutlerRSIStrategy(period=14, min=30.0, max=70.0)",
        ),
        (
            ["--strategy", "exponential-rsi"],
            "ExponentialRSIStrategy(period=14, min=30.0, max=70.0)",
        ),
        (
            ["--strategy", "wilder-rsi"],
            "WilderRSIStrategy(period=14, min=30.0, max=70.0)",
        ),
        (
            [
                "--strategy",
                "mean-reversion",
                "--mean-window",
                "15",
                "--mean-threshold",
                "0.9",
            ],
            "SimpleMeanReversionStrategy(window=15, threshold=0.9)",
        ),
        (
            ["--strategy", "simple-mean-reversion"],
            "SimpleMeanReversionStrategy(window=20, threshold=0.95)",
        ),
        (
            ["--strategy", "exponential-mean-reversion"],
            "ExponentialMeanReversionStrategy(window=20, threshold=0.95)",
        ),
    ],
)
def test_describe_strategy_names_concrete_cli_strategy(
    arguments: list[str],
    expected: str,
) -> None:
    args = parse_args(arguments)

    assert describe_strategy(args.strategy, args) == expected


@pytest.mark.parametrize(
    ("status", "expected_reason"),
    [
        (OrderExecutionStatus.INSUFFICIENT_FUNDS, "Insufficient funds"),
        (OrderExecutionStatus.INSUFFICIENT_POSITION, "Insufficient position"),
    ],
)
def test_print_rejected_orders_uses_execution_status(
    status: OrderExecutionStatus,
    expected_reason: str,
) -> None:
    execution = OrderExecutionResult(
        order=Order(
            symbol="AAPL",
            side=Side.BUY,
            quantity=100,
            signal_timestamp=datetime(2023, 12, 31),
            submitted_timestamp=datetime(2024, 1, 1),
        ),
        status=status,
        trade=None,
    )
    result = BacktestResult(
        symbol="AAPL",
        initial_cash=1_000,
        records=[],
        trades=[],
        order_executions=[execution],
    )
    output = StringIO()

    print_rejected_orders(output, "Rejected orders", result)

    report = output.getvalue()
    assert "Rejected orders: 1" in report
    assert expected_reason in report


def test_rejected_order_details_are_omitted_above_display_limit() -> None:
    rejected_orders = [
        OrderExecutionResult(
            order=Order(
                symbol="AAPL",
                side=Side.BUY,
                quantity=100,
                signal_timestamp=datetime(2023, 12, 31),
                submitted_timestamp=datetime(2024, 1, 1),
            ),
            status=OrderExecutionStatus.INSUFFICIENT_FUNDS,
            trade=None
        )
        for _ in range(MAX_REJECTED_ORDER_DETAILS + 1)
    ]
    result = BacktestResult(
        symbol="AAPL",
        initial_cash=1_000,
        records=[],
        trades=[],
        order_executions=rejected_orders,
    )
    output = StringIO()

    print_rejected_orders(output, "Rejected orders", result)

    report = output.getvalue()
    assert f"Rejected orders: {len(rejected_orders)}" in report
    assert (
        "Details omitted because the rejected-order limit is "
        f"{MAX_REJECTED_ORDER_DETAILS}."
    ) in report
    assert "Order time" not in report


def test_print_metric_comparison_shows_strategy_benchmark_and_difference() -> None:
    output = StringIO()
    strategy_metrics = {
        "total_return": MetricData("Total return", 0.25),
        "number_of_trades": MetricData("Number of trades", 3),
    }
    benchmark_metrics = {
        "total_return": MetricData("Total return", 0.20),
        "number_of_trades": MetricData("Number of trades", 1),
    }
    differences = get_differences(strategy_metrics, benchmark_metrics)

    print_metric_comparison(
        output,
        strategy_metrics,
        benchmark_metrics,
        differences,
    )

    lines = output.getvalue().splitlines()
    assert lines[0] == "Metric comparison"
    assert lines[1].split() == ["Metric", "Strategy", "Benchmark", "Difference"]
    assert lines[2].split() == ["Total", "return", "25.00%", "20.00%", "5.00%"]
    assert lines[3].split() == ["Number", "of", "trades", "3", "1", "2"]


@pytest.mark.parametrize(
    ("name", "value", "expected"),
    [
        ("total_return", 0.12345, "12.35%"),
        ("daily_sharpe_ratio", 1.23456, "1.2346"),
        ("number_of_trades", 3.0, "3"),
        ("daily_sharpe_ratio", float("nan"), "N/A"),
        ("daily_sharpe_ratio", float("inf"), "N/A"),
    ],
)
def test_format_metric_value_uses_metric_specific_formatting(
    name: str,
    value: float,
    expected: str,
) -> None:
    assert format_metric_value(name, value) == expected


