from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Side(Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass(frozen=True)
class Trade:
    symbol: str
    side: Side
    quantity: int
    price: float
    timestamp: datetime