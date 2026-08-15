from typing import List

from ..exceptions.NotEnoughCashException import NotEnoughCashException
from ..portfolio.portfolio import Portfolio
from ..portfolio.trade import Side, Trade


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

    def _buy(self, trade: Trade) -> None:
        if trade.quantity <= 0:
            raise ValueError("Count must be positive.")

        if trade.price <= 0:
            raise ValueError("Price must be positive.")

        cost = trade.price * trade.quantity
        if cost > self.__portfolio.cash:
            raise NotEnoughCashException

        self.__portfolio.cash -= cost
        self.__portfolio.positions[trade.symbol] = self.__portfolio.positions.get(trade.symbol, 0) + trade.quantity

        self.__trades.append(trade)

    def _sell(self, trade: Trade):
        if trade.quantity <= 0:
            raise ValueError("Count must be positive.")

        if trade.price <= 0:
            raise ValueError("Price must be positive.")

        owned = self.__portfolio.positions.get(trade.symbol, 0)

        if trade.quantity > owned:
            raise ValueError("Insufficient position.")

        self.__portfolio.cash += trade.quantity * trade.price
        remaining = owned - trade.quantity

        if remaining == 0:
            del self.__portfolio.positions[trade.symbol]
        else:
            self.__portfolio.positions[trade.symbol] = remaining

        self.__trades.append(trade)

    def execute(self, trade: Trade):
        if trade.side == Side.BUY:
            self._buy(trade)
        else:
            self._sell(trade)





