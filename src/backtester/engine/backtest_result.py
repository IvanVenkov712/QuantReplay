"""Immutable records returned by the backtest engine."""

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from backtester.domain.trading import Signal, Trade, Order


@dataclass(frozen=True)
class OrderExecution:
    """Outcome of an order submitted to the broker during a backtest."""

    order: Order
    success: bool
    reason: Exception | None

@dataclass(frozen=True)
class BacktestRecord:
    """Signal and end-of-period portfolio snapshot for one candle."""

    timestamp: datetime
    generated_signal: Signal
    portfolio_value_at_close: float
    cash: float

@dataclass(frozen=True)
class BacktestResult:
    """Chronological snapshots, successful trades, and attempted orders."""

    records: Sequence[BacktestRecord]
    trades: Sequence[Trade]
    orders: Sequence[OrderExecution]
