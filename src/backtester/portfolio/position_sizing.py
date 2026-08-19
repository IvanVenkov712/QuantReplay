from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable

from portfolio.portfolio import Portfolio
from portfolio.trade import Side

@dataclass(frozen=True)
class SizingContext:
    cash: float
    current_quantity: int
    #portfolio_value: float
    price: float
    side: Side

def make_context(portfolio: Portfolio, side: Side, price: float, symbol: str) -> SizingContext:
    current_quantity = portfolio.position_quantity(symbol)
    cash = portfolio.cash
    return SizingContext(
        cash=cash,
        current_quantity=current_quantity,
        price=price,
        side=side
    )

PositionSizer = Callable[[SizingContext], int]

def all_in_all_out(context: SizingContext) -> int:
    if context.side is Side.BUY:
        return int(context.cash // context.price)

    if context.side is Side.SELL:
        return context.current_quantity

    return 0
