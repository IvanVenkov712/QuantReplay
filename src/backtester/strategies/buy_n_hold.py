from typing import Sequence

from data.models import Candle
from strategies.base import Strategy, Signal


class BuyAndHoldStrategy(Strategy):
    def __init__(self):
        self._buy_signal_generated: bool = False

    def generate_signal(
        self, candles: Sequence[Candle]) -> Signal:
        if not self._buy_signal_generated:
            self._buy_signal_generated = True
            return Signal.BUY

        return Signal.HOLD