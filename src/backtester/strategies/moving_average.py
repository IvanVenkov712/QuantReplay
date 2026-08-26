"""Simple moving-average crossover strategy."""

from typing import Sequence

from backtester.domain.market import Candle
from backtester.strategies.base import Strategy
from backtester.domain.trading import Signal


class MovingAverageCrossStrategy(Strategy):
    """Trade when a short close-price average crosses a longer average.

    A cross above produces a buy and a cross below produces a sell. Signals
    remain on hold until both current and previous windows are available.
    """

    def __init__(self, short_window: int, long_window: int):
        if short_window <= 0 or long_window <= 0:
            raise ValueError("Window sizes must be positive")

        if short_window >= long_window:
            raise ValueError("short_window must be smaller than long_window")

        self.short_window: int = short_window
        self.long_window: int = long_window

    def generate_signal(self, candles: Sequence[Candle]) -> Signal:
        """Generate a crossover signal from the latest available closes."""
        if len(candles) < self.long_window + 1:
            return Signal.HOLD

        old_long_avg = sum(candle.close for candle in candles[-self.long_window - 1:-1]) / self.long_window
        old_short_avg = sum(candle.close for candle in candles[-self.short_window - 1:-1]) / self.short_window

        long_avg = sum(candle.close for candle in candles[-self.long_window:]) / self.long_window
        short_avg = sum(candle.close for candle in candles[-self.short_window:]) / self.short_window

        if old_long_avg <= old_short_avg and long_avg > short_avg:
            return Signal.SELL

        elif old_long_avg >= old_short_avg and long_avg < short_avg:
            return Signal.BUY

        else:
            return Signal.HOLD

