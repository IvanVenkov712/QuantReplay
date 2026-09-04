"""Donchian-channel breakout strategy."""

from collections import deque

from backtester.domain.market import Candle
from backtester.domain.trading import Signal

from backtester.strategies.base import Strategy


class DonchianBreakoutStrategy(Strategy):
    """Generate breakout signals from highs and lows of prior candles.

    A close strictly above the highest high in the previous ``entry_window``
    candles produces a buy signal. A close strictly below the lowest low in
    the previous ``exit_window`` candles produces a sell signal. The strategy
    holds until both channels contain a full window of observations.

    The current candle is added to the channels only after its signal is
    calculated, so its high or low cannot influence its own channel boundary.
    """

    def __init__(self, entry_window: int = 20, exit_window: int = 10) -> None:
        """Initialize the entry and exit channel window sizes."""

        if entry_window <= 0:
            raise ValueError("Positive integer expected for entry_window")
        if exit_window <= 0:
            raise ValueError("Positive integer expected for exit_window")
        self._entry_window = entry_window
        self._exit_window = exit_window

        self._highs: deque[float] = deque(maxlen=entry_window)
        self._lows: deque[float] = deque(maxlen=exit_window)
        self._min = float("+inf")
        self._max = float("-inf")

    def on_candle(self, candle: Candle) -> Signal:
        """Return a signal by comparing the close with the prior channels."""

        signal = Signal.HOLD
        if self._ready():
            if candle.close > self._max:
                signal = Signal.BUY
            elif candle.close < self._min:
                signal = Signal.SELL

        self._update_state(candle)
        return signal

    def _ready(self) -> bool:
        return (
            len(self._highs) >= self._entry_window
            and len(self._lows) >= self._exit_window
        )

    def _update_state(self, candle: Candle) -> None:
        self._lows.append(candle.low)
        self._highs.append(candle.high)
        self._min = min(self._lows)
        self._max = max(self._highs)

    def reset(self) -> None:
        """Discard all prior candles and return to the warm-up state."""

        self._lows.clear()
        self._highs.clear()
        self._min = float("+inf")
        self._max = float("-inf")
