from datetime import datetime
from typing import List

from backtester.portfolio.trade import Trade, Side


class Portfolio:
    __cash: float
    __positions: dict[str, int]
    __trades: List[Trade]

    def __init__(self, cash: float):
        self.__cash = cash
        self.__positions = {}
        self.__trades = []

    @property
    def cash(self) -> float:
        return self.__cash

    @property
    def positions(self) -> dict[str, int]:
        return self.__positions.copy()

    @property
    def trades(self) -> List[Trade]:
        return self.__trades.copy()

    def _buy(self, trade: Trade) -> None:
        if trade.quantity <= 0:
            raise ValueError("Count must be positive.")

        if trade.price <= 0:
            raise ValueError("Price must be positive.")

        cost = trade.quantity * trade.price

        if cost > self.__cash:
            raise ValueError("Insufficient cash.")

        self.__cash -= cost
        self.__positions[trade.symbol] = self.__positions.get(trade.symbol, 0) + trade.quantity

        self.__trades.append(trade)

    def _sell(self, trade: Trade) -> None:
        if trade.quantity <= 0:
            raise ValueError("Count must be positive.")

        if trade.price <= 0:
            raise ValueError("Price must be positive.")

        owned = self.__positions.get(trade.symbol, 0)

        if trade.quantity > owned:
            raise ValueError("Insufficient position.")

        self.__cash += trade.quantity * trade.price
        remaining = owned - trade.quantity

        if remaining == 0:
            del self.__positions[trade.symbol]
        else:
            self.__positions[trade.symbol] = remaining

        self.__trades.append(
            Trade(trade.symbol, Side.SELL, trade.quantity, trade.price, trade.timestamp)
        )

    def apply_trade(self, trade: Trade):
        if trade.side == Side.BUY:
            self._buy(trade)
        elif trade.side == Side.SELL:
            self._sell(trade)


    def value(self, prices: dict[str, float]) -> float:
        return self.cash + sum(
            prices[symbol] *  quantity for symbol, quantity in self.__positions.items()
        )
