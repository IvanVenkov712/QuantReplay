from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from backtester.portfolio.trade import Trade, Order
from backtester.strategies.base import Signal

@dataclass(frozen=True)
class OrderExecution:
    order: Order
    success: bool
    reason: Exception | None

@dataclass(frozen=True)
class BacktestRecord:
    timestamp: datetime
    generated_signal: Signal
    portfolio_value_at_close: float
    cash: float

@dataclass(frozen=True)
class BacktestResult:
    records: Sequence[BacktestRecord]
    trades: Sequence[Trade]
    orders: Sequence[OrderExecution]
