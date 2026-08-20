from abc import ABC, abstractmethod
from dataclasses import dataclass

from backtester.portfolio.trade import Side

@dataclass(frozen=True)
class SizingContext:
    cash: float
    current_quantity: int
    portfolio_value: float
    price: float

class PositionSizer(ABC):
    @abstractmethod
    def calculate_size_buy(self, context: SizingContext) -> int:
        pass

    @abstractmethod
    def calculate_size_sell(self, context: SizingContext) -> int:
        pass

    def calculate_size(self, context: SizingContext, side: Side) -> int:
        if side == Side.BUY:
            return self.calculate_size_buy(context)
        elif side == Side.SELL:
            return self.calculate_size_sell(context)
        else:
            raise ValueError("Unknown side")


class AllInAllOutSizer(PositionSizer):
    def calculate_size_buy(self, context: SizingContext) -> int:
        return int(context.cash // context.price)

    def calculate_size_sell(self, context: SizingContext) -> int:
        return context.current_quantity

class PercentSizer(PositionSizer):
    def __init__(self, percent_buy: float, percent_sell: float):
        if not 0 <= percent_buy <= 1:
            raise ValueError("percent_buy must be between 0 and 1")

        if not 0 <= percent_sell <= 1:
            raise ValueError("percent_sell must be between 0 and 1")

        self._percent_buy = percent_buy
        self._percent_sell = percent_sell

    def calculate_size_buy(self, context: SizingContext) -> int:
        return int(self._percent_buy * context.cash // context.price)

    def calculate_size_sell(self, context: SizingContext) -> int:
        return int(context.current_quantity * self._percent_sell)

