from datetime import datetime

import pytest

from backtester.exceptions.trading_errors import InsufficientPositionError
from backtester.engine.broker import Broker
from backtester.exceptions.trading_errors import InsufficientFundsError
from backtester.portfolio.portfolio import Portfolio
from backtester.portfolio.trade import Side, Trade, Order

TIMESTAMP = datetime(2026, 1, 1)


def make_order(symbol: str, side: Side, quantity: int) -> Order:
    return Order(
        symbol=symbol,
        side=side,
        quantity=quantity,
        #price=price,
        timestamp=TIMESTAMP,
    )


def test_buy_updates_cash_and_position() -> None:
    broker = Broker(Portfolio(cash=1_000, positions={}))
    order = make_order("AAPL", Side.BUY, quantity=10, price=20)

    broker.execute(order)

    assert broker.portfolio.cash == 800
    assert broker.portfolio.positions == {"AAPL": 10}
    assert broker.orders == [trade]


def test_buy_without_enough_cash_raises_and_keeps_state() -> None:
    broker = Broker(Portfolio(cash=100, positions={}))
    order = make_order("AAPL", Side.BUY, quantity=6, price=20)

    with pytest.raises(InsufficientFundsError):
        broker.execute(order)

    assert broker.portfolio.cash == 100
    assert broker.portfolio.positions == {}
    assert broker.trades == []


def test_sell_updates_cash_and_reduces_position() -> None:
    broker = Broker(Portfolio(cash=1_000, positions={}))
    buy_order = make_order("AAPL", Side.BUY, quantity=10, price=20)
    sell_order = make_order("AAPL", Side.SELL, quantity=4, price=25)

    broker.execute(buy_order)
    broker.execute(sell_order)

    assert broker.portfolio.cash == 900
    assert broker.portfolio.positions == {"AAPL": 6}
    assert broker.trades == [buy_trade, sell_trade]


def test_sell_more_shares_than_owned_raises_and_keeps_state() -> None:
    broker = Broker(Portfolio(cash=1_000, positions={}))
    buy_order = make_order("AAPL", Side.BUY, quantity=5, price=20)
    sell_order = make_order("AAPL", Side.SELL, quantity=6, price=25)

    broker.execute(buy_trade)
    with pytest.raises(InsufficientPositionError):
        broker.execute(sell_trade)

    assert broker.portfolio.cash == 900
    assert broker.portfolio.positions == {"AAPL": 5}
    assert broker.trades == [buy_trade]


def test_sell_full_position_removes_symbol() -> None:
    broker = Broker(Portfolio(cash=1_000, positions={}))

    broker.execute(make_trade("AAPL", Side.BUY, quantity=5, price=20))
    broker.execute(make_trade("AAPL", Side.SELL, quantity=5, price=30))

    assert broker.portfolio.cash == 1_050
    assert broker.portfolio.positions == {}


def test_value_with_multiple_positions() -> None:
    broker = Broker(Portfolio(cash=1_000, positions={}))

    broker.execute(make_trade("AAPL", Side.BUY, quantity=10, price=20))
    broker.execute(make_trade("MSFT", Side.BUY, quantity=5, price=40))

    value = broker.portfolio.value({"AAPL": 25, "MSFT": 50})

    assert value == 1_100
