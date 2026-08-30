"""Immutable records returned by the backtest engine."""

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from backtester.domain.market import Candle
from backtester.domain.trading import Signal, Trade, OrderExecutionResult, PortfolioSnapshot


@dataclass(frozen=True)
class BacktestRecord:
    """Signal and end-of-period portfolio snapshot for one candle."""
    candle: Candle
    generated_signal: Signal
    snapshot: PortfolioSnapshot

    @property
    def timestamp(self) -> datetime:
        return self.candle.timestamp

    @property
    def market_value_at_close(self) -> float:
        return self.candle.close

@dataclass(frozen=True)
class BacktestResult:
    """Chronological snapshots, successful trades, and attempted orders."""
    symbol: str
    initial_cash: float
    records: Sequence[BacktestRecord]
    trades: Sequence[Trade]
    order_executions: Sequence[OrderExecutionResult]
