from collections import deque

from backtester.domain.market import Candle
from backtester.domain.trading import Signal

from backtester.strategies.base import Strategy


class DonchianBreakoutStrategy(Strategy):
    def __init__(self, entry_window: int = 20, exit_window: int = 10):
        if entry_window <= 0:
            raise ValueError("Positive integer expected for entry_window")
        if exit_window <= 0:
            raise ValueError("Positive integer expected for exit_window")
        self._entry_window = entry_window
        self._exit_window = exit_window
        
        self._highs = deque(maxlen=entry_window)
        self._lows = deque(maxlen=exit_window)
        self._min = float("+inf")
        self._max = float("-inf")


    def on_candle(self, candle: Candle) -> Signal:
        signal = Signal.HOLD
        if self._ready():
            if candle.close > self._max:
                signal = Signal.BUY
            elif candle.close < self._min:
                signal = Signal.SELL

        self._update_state(candle)
        return signal


    def _ready(self) -> bool:
        return len(self._highs) >= self._entry_window and len(self._lows) >= self._exit_window

    def _update_state(self, candle: Candle):
        self._lows.append(candle.low)
        self._highs.append(candle.high)
        self._min = min(self._lows)
        self._max = max(self._highs)


    def reset(self):
        self._lows.clear()
        self._highs.clear()
        self._min = float("+inf")
        self._max = float("-inf")
