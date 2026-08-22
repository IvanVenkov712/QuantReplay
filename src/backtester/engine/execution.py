from abc import ABC, abstractmethod

from backtester.portfolio.trade import Side


class ExecutionModel:
    def __init__(self, slippage_rate: float):
        if not 0 <= slippage_rate < 1:
            raise ValueError("slippage_rate must be in [0, 1)")

        self._slippage_rate = slippage_rate

    def calculate_fill_price(self, reference_price: float, side: Side) -> float:
        if reference_price <= 0:
            raise ValueError("reference_price must be positive")

        if side == Side.BUY:
            return reference_price * (1 + self._slippage_rate)
        elif side == Side.SELL:
            return reference_price * (1 - self._slippage_rate)
        else:
            raise ValueError("Unknown side")
