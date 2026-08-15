from dataclasses import dataclass
from datetime import datetime
from enum import Enum


@dataclass(frozen=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

