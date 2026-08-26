from __future__ import annotations

import argparse

from backtester.data.loader import CSVDataSource, DataSource, YFinanceDataSource
from backtester.domain.trading import SizingInstruction, SizingMode
from backtester.execution.costs import (
    CommissionModel,
    ExecutionCostCalculator,
    ExecutionModel,
    FixedCommissionModel,
    NoCommissionModel,
    ProportionalCommissionModel,
)
from backtester.metrics.metrics import (
    PerformanceAnalyzer,
    annual_sharpe_ratio,
    annual_volatility,
    annualized_return,
    daily_avg,
    daily_sharpe_ratio,
    daily_volatility,
    max_drawdown,
    number_of_trades,
    total_return,
)
from backtester.resolving.resolver import (
    BufferQuantityResolver,
    BuyQuantityCapper,
    OrderResolver,
    QuantityResolver,
)
from backtester.sizing.policy import SizingPlan
from backtester.strategies.base import Strategy
from backtester.strategies.buy_n_hold import BuyAndHoldStrategy
from backtester.strategies.moving_average import MovingAverageCrossStrategy
from backtester.strategies.mrma import MeanReversionStrategy
from backtester.strategies.rsi_simple import SimpleRSIStrategy


def create_performance_analyzer() -> PerformanceAnalyzer:
    analyzer = PerformanceAnalyzer()
    analyzer.add_metric_func("total_return", "Total return", total_return)
    analyzer.add_metric_func("annualized_return", "Annualized return", annualized_return)
    analyzer.add_metric_func("daily_avg", "Daily average return", daily_avg)
    analyzer.add_metric_func("daily_volatility", "Daily volatility", daily_volatility)
    analyzer.add_metric_func("annual_volatility", "Annual volatility", annual_volatility)
    analyzer.add_metric_func("max_drawdown", "Maximum drawdown", max_drawdown)
    analyzer.add_metric_func(
        "daily_sharpe_ratio",
        "Daily Sharpe ratio",
        daily_sharpe_ratio,
    )
    analyzer.add_metric_func(
        "annual_sharpe_ratio",
        "Annual Sharpe ratio",
        annual_sharpe_ratio,
    )
    analyzer.add_metric_func("number_of_trades", "Number of trades", number_of_trades)
    return analyzer


def create_strategy(name: str, args: argparse.Namespace) -> Strategy:
    if name == "moving-average":
        return MovingAverageCrossStrategy(args.short_window, args.long_window)
    if name == "buy-and-hold":
        return BuyAndHoldStrategy()
    if name == "rsi":
        return SimpleRSIStrategy(args.rsi_period, args.rsi_min, args.rsi_max)
    if name == "mean-reversion":
        return MeanReversionStrategy(args.mean_window, args.mean_threshold)

    raise ValueError(f"Unknown strategy: {name}.")


def create_sizing_plan(args: argparse.Namespace) -> SizingPlan:
    if args.sizing == "all-in-all-out":
        buy_instruction = SizingInstruction(mode=SizingMode.ALL_IN, value=None)
        sell_instruction = SizingInstruction(mode=SizingMode.ALL_IN, value=None)
    elif args.sizing == "fixed":
        buy_instruction = SizingInstruction(
            mode=SizingMode.FIXED,
            value=args.buy_size,
        )
        sell_instruction = SizingInstruction(
            mode=SizingMode.FIXED,
            value=args.sell_size,
        )
    elif args.sizing == "percent":
        buy_instruction = SizingInstruction(
            mode=SizingMode.PERCENT,
            value=args.buy_percent,
        )
        sell_instruction = SizingInstruction(
            mode=SizingMode.PERCENT,
            value=args.sell_percent,
        )
    else:
        raise ValueError(f"Unknown position sizing policy: {args.sizing}.")

    return SizingPlan(buy=buy_instruction, sell=sell_instruction)


def create_order_resolver(
    execution_model: ExecutionModel,
    commission_model: CommissionModel,
    buffer_rate: float | None,
) -> OrderResolver:
    cost_calculator = ExecutionCostCalculator(
        execution_model=execution_model,
        commission_model=commission_model,
    )
    buy_quantity_capper = BuyQuantityCapper(cost_calculator)
    quantity_resolver = QuantityResolver(buy_quantity_capper)

    if buffer_rate is not None:
        quantity_resolver = BufferQuantityResolver(
            resolver=quantity_resolver,
            capper=buy_quantity_capper,
            buffer_rate=buffer_rate,
        )

    return OrderResolver(quantity_resolver)


def create_execution_model(args: argparse.Namespace) -> ExecutionModel:
    return ExecutionModel(slippage_rate=args.slippage_rate)


def create_commission_model(args: argparse.Namespace) -> CommissionModel:
    if args.commission_model == "none":
        return NoCommissionModel()
    if args.commission_model == "fixed":
        return FixedCommissionModel(commission=args.fixed_commission)
    if args.commission_model == "proportional":
        return ProportionalCommissionModel(percent=args.commission_rate)

    raise ValueError(f"Unknown commission model: {args.commission_model}.")


def create_data_source(args: argparse.Namespace) -> DataSource:
    if args.source == "yfinance":
        return YFinanceDataSource()
    if args.source == "csv":
        return CSVDataSource(args.csv_path)

    raise ValueError(f"Unknown data source: {args.source}.")
