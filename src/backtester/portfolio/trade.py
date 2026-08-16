from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from strategies.base import Signal


class Side(Enum):
    BUY = "buy"
    SELL = "sell"

def side_from_signal(signal: Signal):
    if signal == signal.BUY:
        return Side.BUY
    elif signal == signal.SELL:
        return Side.SELL
    else:
        raise ValueError("Invalid signal")

@dataclass(frozen=True)
class Trade:
    symbol: str
    side: Side
    quantity: int
    price: float
    timestamp: datetime

@dataclass(frozen=True)
class Order:
    symbol: str
    side: Side
    quantity: int
    timestamp: datetime