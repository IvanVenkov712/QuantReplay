"""Simple, non-smoothed relative strength index strategy."""
from abc import abstractmethod, ABC
from math import isclose
from typing import Sequence

from backtester.domain.market import Candle
from backtester.strategies.base import Strategy
from backtester.domain.trading import Signal

class RSICalculator(ABC):
    @abstractmethod
    def calculate_rsi(self, curr_price: float) -> float:
        pass

    @abstractmethod
    def reset(self):
        pass

class SimpleRSICalculator(RSICalculator):
    def __init__(self, n: int):
        if n <= 0:
            raise ValueError("Expected positive integer")

        self._n = n
        self._prices: list[float] = []

    def calculate_rsi(self, curr_price: float) -> float:
        self._prices.append(curr_price)
        return calculate_simple_rsi(self._n, self._prices)

    def reset(self):
        self._prices.clear()


def calculate_simple_rsi(n: int, prices: Sequence[float]) -> float:
    """Calculate RSI from simple average gains and losses over ``n`` changes."""

    deltas = [
        curr - prev for
        prev, curr in zip(prices[-n - 1:], prices[-n:])
    ]

    avg_gain = sum(max(delta, 0) for delta in deltas) / n
    avg_loss = sum(max(-delta, 0) for delta in deltas) / n

    if isclose(avg_loss, 0):
        if isclose(avg_gain, 0):
            return 50
        return 100

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return rsi

class RSIStrategy(Strategy):
    """Buy below the lower RSI threshold and sell above the upper threshold."""

    def __init__(self, calculator: RSICalculator, min: float= 30, max: float= 70, ):
        if not 0 <= min <= max <= 100:
            raise ValueError("0 <= min <= max <= 100")

        self._min: float = min
        self._max: float = max
        self._calculator = calculator

    def on_candle(self, candle: Candle) -> Signal:
        """Generate a threshold signal from the latest RSI value calculated with the RSICalculator."""

        rsi = self._calculator.calculate_rsi(candle.close)

        if rsi < self._min:
            return Signal.BUY
        elif rsi > self._max:
            return Signal.SELL
        else:
            return Signal.HOLD

    def reset(self):
        self._calculator.reset()
