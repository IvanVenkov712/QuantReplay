from abc import ABC, abstractmethod
from enum import Enum
from typing import Sequence

from backtester.data.models import Candle


class Signal(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

class Strategy(ABC):

    @abstractmethod
    def generate_signal(
        self, candles: Sequence[Candle]) -> Signal:
        pass


