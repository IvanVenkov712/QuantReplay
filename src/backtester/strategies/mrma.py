"""Moving-average mean-reversion strategy."""

from typing import Sequence

from backtester.domain.market import Candle
from backtester.strategies.base import Strategy
from backtester.domain.trading import Signal


class MeanReversionStrategy(Strategy):
    """Buy below a fraction of the rolling mean and sell at or above it."""

    def __init__(self, window: int, threshold: float):
        if not window > 0:
            raise ValueError("window must be positive integer")

        if not 0 <= threshold <= 1:
            raise ValueError("threshold must be between 0 and 1")

        self.__window: int = window
        self.__threshold: float = threshold

    def generate_signal(
        self, candles: Sequence[Candle]) -> Signal:
        """Generate a signal from the latest close and rolling close mean."""

        if len(candles) < self.__window:
            return Signal.HOLD

        average = sum(candle.close for candle in candles[-self.__window:]) / self.__window
        price = candles[-1].close

        if price < average * self.__threshold:
            return Signal.BUY
        elif price >= average:
            return Signal.SELL
        else:
            return Signal.HOLD
