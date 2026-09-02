"""High-level workflows executed by QuantReplay CLI commands."""

from __future__ import annotations

import argparse
from datetime import date
from typing import Sequence, TextIO

from backtester.cli import factories, reporting
from backtester.data.loader import candles_from_dataframe
from backtester.domain.market import Candle
from backtester.engine.backtest import BacktestEngine
from backtester.engine.backtest_result import BacktestResult
from backtester.execution.broker import Broker
from backtester.execution.costs import CommissionModel, ExecutionModel
from backtester.metrics.benchmark_comparison import get_differences
from backtester.portfolio.portfolio import Portfolio
from backtester.sizing.policy import SizingPlan
from backtester.strategies.base import Strategy
from backtester.visualization.export import export_backtest_dashboard


def run_backtest_command(args: argparse.Namespace, output: TextIO) -> None:
    """Run one configured backtest and print its parameters and results."""
    start, end = resolve_date_range(args.start, args.end, args.years)
    strategy = factories.create_strategy(args.strategy, args)
    result = _run_backtest(args, strategy, start, end)
    metrics = factories.create_performance_analyzer().calculate_metrics(result)

    reporting.print_parameters(
        output=output,
        title="Backtest parameters",
        strategy_name=reporting.describe_strategy(args.strategy, args),
        benchmark_name=None,
        symbol=args.symbol,
        start=start,
        end=end,
        years=args.years,
        data_source_name=reporting.describe_data_source(args),
        initial_capital=args.initial_capital,
        sizing_name=reporting.describe_sizing(args),
        commission_name=reporting.describe_commission(args),
        slippage_name=reporting.describe_slippage(args),
    )
    reporting.print_metrics(output, "Performance metrics", metrics)
    reporting.print_rejected_orders(output, "Rejected orders", result)

    if args.chart_path is not None:
        chart_path = export_backtest_dashboard(result, args.chart_path)
        print(file=output)
        print(f"Chart saved to: {chart_path}", file=output)


def run_compare_command(args: argparse.Namespace, output: TextIO) -> None:
    """Run a strategy and benchmark over identical data and print differences."""
    start, end = resolve_date_range(args.start, args.end, args.years)
    data_source = factories.create_data_source(args)
    data = data_source.load(args.symbol, start, end)
    if data is None or data.empty:
        raise ValueError("No market data was returned for the selected parameters.")

    candles = candles_from_dataframe(data)
    _validate_backtest_data(candles)

    strategy_result = _run_backtest_with_candles(
        strategy=factories.create_strategy(args.strategy, args),
        candles=candles,
        symbol=args.symbol,
        initial_capital=args.initial_capital,
        sizing_plan=factories.create_sizing_plan(args),
        execution_model=factories.create_execution_model(args),
        commission_model=factories.create_commission_model(args),
        buffer_rate=args.buffer_rate,
    )
    benchmark_result = _run_backtest_with_candles(
        strategy=factories.create_strategy(args.benchmark, args),
        candles=candles,
        symbol=args.symbol,
        initial_capital=args.initial_capital,
        sizing_plan=factories.create_sizing_plan(args),
        execution_model=factories.create_execution_model(args),
        commission_model=factories.create_commission_model(args),
        buffer_rate=args.buffer_rate,
    )

    analyzer = factories.create_performance_analyzer()
    strategy_metrics = analyzer.calculate_metrics(strategy_result)
    benchmark_metrics = analyzer.calculate_metrics(benchmark_result)
    differences = get_differences(strategy_metrics, benchmark_metrics)

    reporting.print_parameters(
        output=output,
        title="Benchmark comparison parameters",
        strategy_name=reporting.describe_strategy(args.strategy, args),
        benchmark_name=reporting.describe_strategy(args.benchmark, args),
        symbol=args.symbol,
        start=start,
        end=end,
        years=args.years,
        data_source_name=reporting.describe_data_source(args),
        initial_capital=args.initial_capital,
        sizing_name=reporting.describe_sizing(args),
        commission_name=reporting.describe_commission(args),
        slippage_name=reporting.describe_slippage(args),
    )
    reporting.print_metric_comparison(
        output,
        strategy_metrics,
        benchmark_metrics,
        differences,
    )
    reporting.print_rejected_orders(
        output,
        "Strategy rejected orders",
        strategy_result,
    )
    reporting.print_rejected_orders(
        output,
        "Benchmark rejected orders",
        benchmark_result,
    )


def _run_backtest(
    args: argparse.Namespace,
    strategy: Strategy,
    start: str,
    end: str,
) -> BacktestResult:
    data_source = factories.create_data_source(args)
    data = data_source.load(args.symbol, start, end)
    if data is None or data.empty:
        raise ValueError("No market data was returned for the selected parameters.")

    candles = candles_from_dataframe(data)
    _validate_backtest_data(candles)
    return _run_backtest_with_candles(
        strategy=strategy,
        candles=candles,
        symbol=args.symbol,
        initial_capital=args.initial_capital,
        sizing_plan=factories.create_sizing_plan(args),
        execution_model=factories.create_execution_model(args),
        commission_model=factories.create_commission_model(args),
        buffer_rate=args.buffer_rate,
    )


def _run_backtest_with_candles(
    strategy: Strategy,
    candles: Sequence[Candle],
    symbol: str,
    initial_capital: float,
    sizing_plan: SizingPlan,
    execution_model: ExecutionModel,
    commission_model: CommissionModel,
    buffer_rate: float | None,
) -> BacktestResult:
    broker = Broker(
        Portfolio(cash=initial_capital),
        execution_model=execution_model,
        commission_model=commission_model,
    )
    return BacktestEngine(
        strategy=strategy,
        broker=broker,
        plan=sizing_plan,
        resolver=factories.create_order_resolver(
            execution_model=execution_model,
            commission_model=commission_model,
            buffer_rate=buffer_rate,
        ),
        data=candles,
        symbol=symbol,
    ).run()


def resolve_date_range(
    start_arg: str | None,
    end_arg: str | None,
    years: int,
) -> tuple[str, str]:
    """Resolve an inclusive start and exclusive end date for data loading.

    Missing end dates default to today. A missing start is derived by
    subtracting ``years`` from the end, with February 29 adjusted to February
    28 when the target year is not a leap year.
    """
    end = date.fromisoformat(end_arg) if end_arg else date.today()
    start = date.fromisoformat(start_arg) if start_arg else _subtract_years(end, years)

    if start >= end:
        raise ValueError("Start date must be before end date.")

    return start.isoformat(), end.isoformat()


def _subtract_years(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year - years)
    except ValueError:
        return value.replace(year=value.year - years, day=28)


def _validate_backtest_data(candles: Sequence[Candle]) -> None:
    if len(candles) < 2:
        raise ValueError("At least two candles are required to calculate metrics.")
