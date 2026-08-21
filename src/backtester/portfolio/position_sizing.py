from abc import ABC, abstractmethod
from dataclasses import dataclass

from backtester.portfolio.trade import Side

@dataclass(frozen=True)
class SizingContext:
    """Portfolio snapshot available when a signal is converted into an order."""

    cash: float
    current_quantity: int
    portfolio_value: float
    price: float

    def __post_init__(self):
        if self.cash < 0:
            raise ValueError("cash cannot be negative")

        if self.current_quantity < 0:
            raise ValueError("current quantity cannot be negative")

        if self.portfolio_value < self.cash:
            raise ValueError("portfolio value cannot be less than cash")

        if self.price <= 0:
            raise ValueError("price must be positive")

class PositionSizer(ABC):
    """Convert buy and sell signals into whole-share order quantities."""

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

class FixedSizer(PositionSizer):
    """Return configured share quantities for every buy and sell signal."""

    def __init__(self, buy_size: int, sell_size: int):
        self._buy_size: int = buy_size
        self._sell_size: int = sell_size

    def calculate_size_buy(self, context: SizingContext) -> int:
        return self._buy_size

    def calculate_size_sell(self, context: SizingContext) -> int:
        return self._sell_size

class AllInAllOutSizer(PositionSizer):
    """Buy the affordable whole shares or sell the entire current position."""

    def calculate_size_buy(self, context: SizingContext) -> int:
        return int(context.cash // context.price)

    def calculate_size_sell(self, context: SizingContext) -> int:
        return context.current_quantity

class PercentSizer(PositionSizer):
    """Size buys from available cash and sells from the current position."""

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

