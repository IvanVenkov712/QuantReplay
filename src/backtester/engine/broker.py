from datetime import datetime
from typing import List

from backtester.exceptions.trading_errors import (
    PriceNotFoundError,
    InsufficientFundsError,
    InsufficientPositionError,
)
from backtester.portfolio.portfolio import Portfolio
from backtester.portfolio.trade import Side, Trade, Order


class Broker:
    __trades: List[Trade]
    __portfolio: Portfolio

    def __init__(self, portfolio: Portfolio):
        self.__portfolio = portfolio
        self.__trades = []

    @property
    def portfolio(self) -> Portfolio:
        return self.__portfolio

    @property
    def trades(self) -> List[Trade]:
        return self.__trades.copy()

    def _buy(self, order: Order, price: float) -> None:
        if price <= 0:
            raise ValueError("Price must be positive.")

        cost = price * order.quantity
        if cost > self.__portfolio.cash:
            raise InsufficientFundsError

        self.__portfolio.cash -= cost
        self.__portfolio.add_position(order.symbol, order.quantity)

    def _sell(self, order: Order, price: float):
        if price <= 0:
            raise ValueError("Price must be positive.")

        owned = self.__portfolio.position_quantity(order.symbol)

        if order.quantity > owned:
            raise InsufficientPositionError

        self.__portfolio.cash += order.quantity * price
        self.__portfolio.remove_position(order.symbol, order.quantity)

    def execute(self, order: Order, prices: dict[str, float], timestamp: datetime):
        if not order.symbol in prices:
            raise PriceNotFoundError
        price = prices[order.symbol]
        if order.side == Side.BUY:
            self._buy(order, price)
        elif order.side == Side.SELL:
            self._sell(order, price)

        self.__trades.append(Trade(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=price,
            timestamp=timestamp
        ))





