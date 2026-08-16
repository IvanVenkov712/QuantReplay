from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from portfolio.trade import Trade, Order
from strategies.base import Signal

@dataclass(frozen=True)
class OrderExecution:
    order: Order
    success: bool
    reason: Exception | None

@dataclass(frozen=True)
class BacktestRecord:
    timestamp: datetime
    signal: Signal
    portfolio_value: float
    cash: float

@dataclass(frozen=True)
class BacktestResult:
    records: Sequence[BacktestRecord]
    trades: Sequence[Trade]
    orders: Sequence[OrderExecution]