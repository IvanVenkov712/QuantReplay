from math import isclose
from typing import Sequence

from backtester.domain.market import Candle
from backtester.strategies.base import Strategy
from backtester.domain.trading import Signal


def calculate_simple_rsi(n: int, candles: Sequence[Candle]) -> float:

    deltas = [
        curr.close - prev.close for
        prev, curr in zip(candles[-n - 1:], candles[-n:])
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

class SimpleRSIStrategy(Strategy):
    def __init__(self, n: int = 14, min: float= 30, max: float= 70):
        if n <= 1:
            raise ValueError("n must be greater than 1")

        if not 0 <= min <= max <= 100:
            raise ValueError("0 <= min <= max <= 100")

        self.__n: int = n
        self.__min: float = min
        self.__max: float = max

    def generate_signal(
        self, candles: Sequence[Candle]) -> Signal:

        if len(candles) < self.__n + 1:
            return Signal.HOLD

        rsi = calculate_simple_rsi(self.__n, candles)

        if rsi < self.__min:
            return Signal.BUY
        elif rsi > self.__max:
            return Signal.SELL
        else:
            return Signal.HOLD


