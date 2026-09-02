from pathlib import Path

from backtester.data.loader import CSVDataSource, candles_from_dataframe
from backtester.domain.trading import SizingInstruction, SizingMode
from backtester.engine.backtest import BacktestEngine
from backtester.engine.backtest_result import BacktestResult
from backtester.execution.broker import Broker
from backtester.execution.costs import ExecutionModel, ProportionalCommissionModel, ExecutionCostCalculator, \
    NoCommissionModel
from backtester.portfolio.portfolio import Portfolio
from backtester.resolving.resolver import OrderResolver, QuantityResolver, BuyQuantityCapper
from backtester.sizing.policy import SizingPlan
from backtester.strategies.buy_n_hold import BuyAndHoldStrategy
from backtester.strategies.moving_average import SimpleMovingAverageCrossStrategy
from backtester.strategies.mrma import ExponentialMeanReversionStrategy
from backtester.strategies.rsi_strategies import WilderRSIStrategy


def load_results() -> BacktestResult:
    source = CSVDataSource(Path("../../../data") / "MSFT.csv")
    data = source.load("MSFT", "2021-01-01", "2026-01-01")
    candles = candles_from_dataframe(data)

    exec_model = ExecutionModel(0.00001)
    comm_model = ProportionalCommissionModel(0.00001)
    cost_calculator = ExecutionCostCalculator(exec_model, comm_model)
    broker = Broker(
        execution_model=exec_model,
        commission_model=comm_model,
        portfolio=Portfolio(10000)
    )
    resolver = OrderResolver(QuantityResolver(BuyQuantityCapper(cost_calculator)))
    plan = SizingPlan(
        SizingInstruction(None, SizingMode.ALL_IN),
        SizingInstruction(None, SizingMode.ALL_IN)
    )

    engine = BacktestEngine(
        WilderRSIStrategy(30, 70),
        broker,
        plan,
        resolver,
        candles,
        "MSFT"
    )
    return engine.run()