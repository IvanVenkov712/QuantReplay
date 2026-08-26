"""Buy-and-hold strategy implementation."""

from typing import Sequence

from backtester.domain.market import Candle
from backtester.strategies.base import Strategy
from backtester.domain.trading import Signal


class BuyAndHoldStrategy(Strategy):
    """Emit one buy signal on the first call and hold thereafter."""

    def __init__(self):
        self._buy_signal_generated: bool = False

    def generate_signal(
        self, candles: Sequence[Candle]) -> Signal:
        """Return the strategy's one initial buy or a subsequent hold."""
        if not self._buy_signal_generated:
            self._buy_signal_generated = True
            return Signal.BUY

        return Signal.HOLD
