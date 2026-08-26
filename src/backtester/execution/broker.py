from datetime import datetime
from typing import List

from backtester.exceptions.trading_errors import (
    PriceNotFoundError,
    InsufficientFundsError,
    InsufficientPositionError,
)
from backtester.execution.costs import CommissionModel, ExecutionModel
from backtester.portfolio.portfolio import Portfolio
from backtester.domain.trading import Side, Trade, Order


class Broker:
    __trades: List[Trade]
    __portfolio: Portfolio
    __execution_model: ExecutionModel
    __commission_model: CommissionModel

    def __init__(self, portfolio: Portfolio,
                 execution_model: ExecutionModel,
                 commission_model: CommissionModel
        ):
        self.__portfolio = portfolio
        self.__trades = []
        self.__execution_model = execution_model
        self.__commission_model = commission_model

    @property
    def portfolio(self) -> Portfolio:
        return self.__portfolio

    @property
    def trades(self) -> List[Trade]:
        return self.__trades.copy()

    def _buy(self, order: Order, fill_price: float, commission: float) -> None:
        if fill_price <= 0:
            raise ValueError("Price must be positive.")

        cost = fill_price * order.quantity + commission
        if cost > self.__portfolio.cash:
            raise InsufficientFundsError

        self.__portfolio.cash -= cost
        self.__portfolio.add_position(order.symbol, order.quantity)

    def _sell(self, order: Order, fill_price: float, commission: float):
        if fill_price <= 0:
            raise ValueError("Price must be positive.")

        owned = self.__portfolio.position_quantity(order.symbol)

        if order.quantity > owned:
            raise InsufficientPositionError

        new_cash = self.__portfolio.cash + order.quantity * fill_price - commission
        if new_cash < 0:
            raise InsufficientFundsError("Not enough cash for the commission")

        self.__portfolio.cash = new_cash
        self.__portfolio.remove_position(order.symbol, order.quantity)

    def execute(self, order: Order, prices: dict[str, float], timestamp: datetime) -> Trade:
        if not order.symbol in prices:
            raise PriceNotFoundError

        fill_price = self.__execution_model.calculate_fill_price(prices[order.symbol], order.side)
        commission = self.__commission_model.calculate(order.quantity, fill_price)

        trade = Trade(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            fill_price=fill_price,
            commission=commission,
            timestamp=timestamp
        )
        _validate_timestamp(timestamp=timestamp)

        if order.side == Side.BUY:
            self._buy(order, fill_price, commission)
        elif order.side == Side.SELL:
            self._sell(order, fill_price, commission)
        else:
            raise ValueError("Invalid order side")
       
        self.__trades.append(trade)
        return trade

def _validate_timestamp(timestamp: datetime) -> None:
    if not isinstance(timestamp, datetime):
        raise ValueError("Timestamp must be a datetime.")
