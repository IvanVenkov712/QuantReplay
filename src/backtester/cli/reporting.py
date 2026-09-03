"""Plain-text formatting and reporting for CLI backtest results."""

from __future__ import annotations

import argparse
import math
from datetime import datetime
from typing import TextIO

from backtester.domain.trading import OrderExecutionStatus
from backtester.engine.backtest_result import BacktestResult
from backtester.metrics.metrics import MetricData


MAX_REJECTED_ORDER_DETAILS = 10

PERCENT_METRICS = {
    "total_return",
    "annualized_return",
    "daily_avg",
    "daily_volatility",
    "annual_volatility",
    "max_drawdown",
}

REJECTION_MESSAGES = {
    OrderExecutionStatus.INSUFFICIENT_FUNDS: "Insufficient funds",
    OrderExecutionStatus.INSUFFICIENT_POSITION: "Insufficient position",
}


def print_parameters(
    *,
    output: TextIO,
    title: str,
    strategy_name: str,
    benchmark_name: str | None,
    symbol: str,
    start: str,
    end: str,
    years: int,
    years_note: str,
    csv_period_anchor: str | None,
    csv_period_anchor_applied: bool,
    result: BacktestResult,
    data_source_name: str,
    initial_capital: float,
    sizing_name: str,
    commission_name: str,
    slippage_name: str,
) -> None:
    """Print the effective parameters of a backtest or comparison."""
    print(title, file=output)
    print(f"Strategy: {strategy_name}", file=output)
    if benchmark_name is not None:
        print(f"Benchmark: {benchmark_name}", file=output)
    print(f"Asset: {symbol}", file=output)
    print(
        f"Requested period: {start} (inclusive) to {end} (exclusive)",
        file=output,
    )
    _print_data_period(output, result)
    print(f"Years parameter: {years} ({years_note})", file=output)
    if csv_period_anchor is not None:
        if csv_period_anchor_applied and csv_period_anchor == "end-csv":
            anchor_note = "applied; final CSV candle included"
        elif csv_period_anchor_applied:
            anchor_note = "applied"
        else:
            anchor_note = "not applied because a date boundary was provided"
        print(
            f"CSV period anchor: {csv_period_anchor} ({anchor_note})",
            file=output,
        )
    print(f"Data source: {data_source_name}", file=output)
    print(f"Initial capital: {_format_money(initial_capital)}", file=output)
    print(f"Position sizing: {sizing_name}", file=output)
    print(f"Commission: {commission_name}", file=output)
    print(f"Slippage: {slippage_name}", file=output)
    print(file=output)


def _print_data_period(output: TextIO, result: BacktestResult) -> None:
    """Print the actual candle coverage used by the backtest."""
    first_timestamp = result.records[0].timestamp
    last_timestamp = result.records[-1].timestamp
    observation_count = len(result.records)

    print(
        "Data used: "
        f"{_format_date(first_timestamp)} through {_format_date(last_timestamp)} "
        f"({observation_count:,} candles)",
        file=output,
    )

    elapsed_days = (
        last_timestamp - first_timestamp
    ).total_seconds() / (24.0 * 60.0 * 60.0)
    elapsed_years = elapsed_days / 365.25
    print(
        f"Data span: {_format_day_count(elapsed_days)} calendar "
        f"{'day' if elapsed_days == 1 else 'days'} "
        f"({elapsed_years:.2f} years)",
        file=output,
    )


def _format_date(value: datetime) -> str:
    return value.date().isoformat()


def _format_day_count(value: float) -> str:
    if value.is_integer():
        return f"{int(value):,}"
    return f"{value:,.2f}"


def print_metrics(
    output: TextIO,
    title: str,
    metrics: dict[str, MetricData],
) -> None:
    """Print labeled metric values in analyzer registration order."""
    print(title, file=output)
    for name, data in metrics.items():
        print(f"{data.label}: {format_metric_value(name, data.result)}", file=output)


def print_metric_comparison(
    output: TextIO,
    strategy_metrics: dict[str, MetricData],
    benchmark_metrics: dict[str, MetricData],
    differences: dict[str, MetricData],
) -> None:
    """Print common metrics and their strategy-minus-benchmark differences."""
    rows: list[tuple[str, str, str, str]] = []
    for name, difference_data in differences.items():
        strategy_data = strategy_metrics.get(name)
        benchmark_data = benchmark_metrics.get(name)
        if strategy_data is None or benchmark_data is None:
            continue

        rows.append(
            (
                strategy_data.label,
                format_metric_value(name, strategy_data.result),
                format_metric_value(name, benchmark_data.result),
                format_metric_value(name, difference_data.result),
            )
        )

    headers = ("Metric", "Strategy", "Benchmark", "Difference")
    widths = [
        max(len(header), *(len(row[index]) for row in rows))
        for index, header in enumerate(headers)
    ]

    print("Metric comparison", file=output)
    print(
        f"{headers[0]:<{widths[0]}}  "
        f"{headers[1]:>{widths[1]}}  "
        f"{headers[2]:>{widths[2]}}  "
        f"{headers[3]:>{widths[3]}}",
        file=output,
    )
    for label, strategy_value, benchmark_value, difference_value in rows:
        print(
            f"{label:<{widths[0]}}  "
            f"{strategy_value:>{widths[1]}}  "
            f"{benchmark_value:>{widths[2]}}  "
            f"{difference_value:>{widths[3]}}",
            file=output,
        )


def print_rejected_orders(
    output: TextIO,
    title: str,
    result: BacktestResult,
) -> None:
    """Print a bounded summary of orders rejected during a backtest."""
    rejected_orders = [
        execution
        for execution in result.order_executions
        if execution.status is not OrderExecutionStatus.SUCCESS
    ]
    if not rejected_orders:
        return

    print(file=output)
    print(f"{title}: {len(rejected_orders)}", file=output)

    if len(rejected_orders) > MAX_REJECTED_ORDER_DETAILS:
        print(
            "Details omitted because the rejected-order limit is "
            f"{MAX_REJECTED_ORDER_DETAILS}.",
            file=output,
        )
        return

    for execution in rejected_orders:
        order = execution.order
        print(
            "- Order time "
            f"{order.submitted_timestamp.isoformat(sep=' ')} | "
            f"{order.side.value.upper()} {order.quantity} {order.symbol} | "
            f"{_format_rejection_status(execution.status)}",
            file=output,
        )


def _format_rejection_status(status: OrderExecutionStatus) -> str:
    return REJECTION_MESSAGES.get(status, "Unknown rejection reason")


def format_metric_value(name: str, value: float) -> str:
    """Format a metric according to its semantic type for CLI output."""
    if isinstance(value, float) and not math.isfinite(value):
        return "N/A"

    if name in PERCENT_METRICS:
        return f"{value:.2%}"

    if name == "number_of_trades":
        return str(int(value))

    return f"{value:.4f}"


def _format_money(value: float) -> str:
    return f"{value:,.2f}"


def describe_strategy(name: str, args: argparse.Namespace) -> str:
    """Return a concise description of a configured strategy."""
    if name in {"moving-average", "simple-moving-average"}:
        return (
            "SimpleMovingAverageCrossStrategy("
            f"{args.short_window}, {args.long_window})"
        )
    if name == "exponential-moving-average":
        return (
            "ExponentialMovingAverageCrossStrategy("
            f"{args.short_window}, {args.long_window})"
        )
    if name == "buy-and-hold":
        return "BuyAndHoldStrategy"
    if name in {"rsi", "cutler-rsi"}:
        return (
            f"CutlerRSIStrategy(period={args.rsi_period}, "
            f"min={args.rsi_min}, max={args.rsi_max})"
        )
    if name == "exponential-rsi":
        return (
            f"ExponentialRSIStrategy(period={args.rsi_period}, "
            f"min={args.rsi_min}, max={args.rsi_max})"
        )
    if name == "wilder-rsi":
        return (
            f"WilderRSIStrategy(period={args.rsi_period}, "
            f"min={args.rsi_min}, max={args.rsi_max})"
        )
    if name in {"mean-reversion", "simple-mean-reversion"}:
        return (
            f"SimpleMeanReversionStrategy(window={args.mean_window}, "
            f"threshold={args.mean_threshold})"
        )
    if name == "exponential-mean-reversion":
        return (
            f"ExponentialMeanReversionStrategy(window={args.mean_window}, "
            f"threshold={args.mean_threshold})"
        )

    raise ValueError(f"Unknown strategy: {name}.")


def describe_data_source(args: argparse.Namespace) -> str:
    """Return a concise description of the configured data source."""
    if args.source == "yfinance":
        return "YFinanceDataSource"

    return f"CSVDataSource({args.csv_path})"


def describe_sizing(args: argparse.Namespace) -> str:
    """Return a concise description of sizing and any cash buffer."""
    if args.sizing == "all-in-all-out":
        description = "all-in-all-out"
    elif args.sizing == "fixed":
        description = f"fixed (buy={args.buy_size}, sell={args.sell_size})"
    elif args.sizing == "percent":
        description = (
            "percent ("
            f"buy={args.buy_percent:.2%}, sell={args.sell_percent:.2%}"
            ")"
        )
    else:
        raise ValueError(f"Unknown position sizing policy: {args.sizing}.")

    if args.buffer_rate is not None:
        return f"{description}, buffer={args.buffer_rate:.2%}"

    return description


def describe_commission(args: argparse.Namespace) -> str:
    """Return a concise description of the configured commission model."""
    if args.commission_model == "none":
        return "NoCommissionModel"
    if args.commission_model == "fixed":
        return (
            "FixedCommissionModel("
            f"per_trade={_format_money(args.fixed_commission)}"
            ")"
        )
    if args.commission_model == "proportional":
        return f"ProportionalCommissionModel(rate={args.commission_rate:.2%})"

    raise ValueError(f"Unknown commission model: {args.commission_model}.")


def describe_slippage(args: argparse.Namespace) -> str:
    """Return a concise description of the configured slippage rate."""
    return f"ExecutionModel(rate={args.slippage_rate:.2%})"
