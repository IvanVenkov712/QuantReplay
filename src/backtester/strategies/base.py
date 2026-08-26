from abc import ABC, abstractmethod
from typing import Sequence

from backtester.domain.market import Candle
from backtester.domain.trading import Signal


class Strategy(ABC):

    @abstractmethod
    def generate_signal(
        self, candles: Sequence[Candle]) -> Signal:
        pass


