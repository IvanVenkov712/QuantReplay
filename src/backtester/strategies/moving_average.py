"""Simple moving-average crossover strategy."""
from collections import deque

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

        self._short_window_len: int = short_window
        self._long_window_len: int = long_window

        self._long_sum: float= 0
        self._short_sum: float = 0

        self._long_window = deque(maxlen=self._long_window_len)
        self._short_window = deque(maxlen=self._short_window_len)

        self._counter = 0

    def on_candle(self, candle: Candle) -> Signal:
        old_long_avg = self._long_sum / self._long_window_len
        old_short_avg = self._short_sum / self._short_window_len

        self._update_state(candle.close)

        if self._counter < self._long_window_len:
            self._counter += 1
            return Signal.HOLD

        new_long_avg = self._long_sum / self._long_window_len
        new_short_avg = self._short_sum / self._short_window_len

        if old_short_avg >= old_long_avg and new_short_avg < new_long_avg:
            return Signal.SELL

        elif old_short_avg <= old_long_avg and new_short_avg > new_long_avg:
            return Signal.BUY

        else:
            return Signal.HOLD

    def _update_state(self, price: float):
        if len(self._long_window) >= self._long_window_len:
            self._long_sum -= self._long_window.popleft()

        if len(self._short_window) >= self._short_window_len:
            self._short_sum -= self._short_window.popleft()

        self._long_sum += price
        self._short_sum += price
        self._long_window.append(price)
        self._short_window.append(price)

    def reset(self):
        self._long_sum: float = 0
        self._short_sum: float = 0

        self._long_window = deque(maxlen=self._long_window_len)
        self._short_window = deque(maxlen=self._short_window_len)

        self._counter = 0