from datetime import datetime

import pytest

from backtester.engine.broker import Broker
from backtester.exceptions.trading_errors import (
    ActiveNotFoundError,
    InsufficientFundsError,
    InsufficientPositionError,
)
from backtester.portfolio.portfolio import Portfolio
from backtester.portfolio.trade import Order, Side, Trade


ORDER_TIMESTAMP = datetime(2026, 1, 1, 9, 30)
EXECUTION_TIMESTAMP = datetime(2026, 1, 1, 9, 31)


def make_order(symbol: str, side: Side, quantity: int) -> Order:
    return Order(
        symbol=symbol,
        side=side,
        quantity=quantity,
        timestamp=ORDER_TIMESTAMP,
    )


def execute_order(
    broker: Broker,
    order: Order,
    price: float,
    timestamp: datetime = EXECUTION_TIMESTAMP,
) -> None:
    broker.execute(order, prices={order.symbol: price}, timestamp=timestamp)


def test_buy_order_uses_market_price_and_records_trade() -> None:
    broker = Broker(Portfolio(cash=1_000, positions={}))
    order = make_order("AAPL", Side.BUY, quantity=10)

    execute_order(broker, order, price=20)

    expected_trade = Trade(
        symbol="AAPL",
        side=Side.BUY,
        quantity=10,
        price=20,
        timestamp=EXECUTION_TIMESTAMP,
    )
    assert broker.portfolio.cash == 800
    assert broker.portfolio.positions == {"AAPL": 10}
    assert broker.trades == [expected_trade]


def test_buy_without_enough_cash_raises_and_keeps_state() -> None:
    broker = Broker(Portfolio(cash=100, positions={}))
    order = make_order("AAPL", Side.BUY, quantity=6)

    with pytest.raises(InsufficientFundsError):
        execute_order(broker, order, price=20)

    assert broker.portfolio.cash == 100
    assert broker.portfolio.positions == {}
    assert broker.trades == []


def test_sell_order_uses_market_price_and_reduces_position() -> None:
    broker = Broker(Portfolio(cash=1_000, positions={}))
    buy_order = make_order("AAPL", Side.BUY, quantity=10)
    sell_order = make_order("AAPL", Side.SELL, quantity=4)

    execute_order(broker, buy_order, price=20)
    execute_order(broker, sell_order, price=25)

    assert broker.portfolio.cash == 900
    assert broker.portfolio.positions == {"AAPL": 6}
    assert broker.trades == [
        Trade("AAPL", Side.BUY, quantity=10, price=20, timestamp=EXECUTION_TIMESTAMP),
        Trade("AAPL", Side.SELL, quantity=4, price=25, timestamp=EXECUTION_TIMESTAMP),
    ]


def test_sell_more_shares_than_owned_raises_and_keeps_state() -> None:
    broker = Broker(Portfolio(cash=1_000, positions={}))
    buy_order = make_order("AAPL", Side.BUY, quantity=5)
    sell_order = make_order("AAPL", Side.SELL, quantity=6)

    execute_order(broker, buy_order, price=20)
    with pytest.raises(InsufficientPositionError):
        execute_order(broker, sell_order, price=25)

    assert broker.portfolio.cash == 900
    assert broker.portfolio.positions == {"AAPL": 5}
    assert broker.trades == [
        Trade("AAPL", Side.BUY, quantity=5, price=20, timestamp=EXECUTION_TIMESTAMP)
    ]


def test_sell_full_position_removes_symbol() -> None:
    broker = Broker(Portfolio(cash=1_000, positions={}))

    execute_order(broker, make_order("AAPL", Side.BUY, quantity=5), price=20)
    execute_order(broker, make_order("AAPL", Side.SELL, quantity=5), price=30)

    assert broker.portfolio.cash == 1_050
    assert broker.portfolio.positions == {}


def test_execute_rejects_missing_market_price_and_keeps_state() -> None:
    broker = Broker(Portfolio(cash=1_000, positions={}))
    order = make_order("AAPL", Side.BUY, quantity=1)

    with pytest.raises(ActiveNotFoundError):
        broker.execute(
            order,
            prices={"MSFT": 20},
            timestamp=EXECUTION_TIMESTAMP,
        )

    assert broker.portfolio.cash == 1_000
    assert broker.portfolio.positions == {}
    assert broker.trades == []


@pytest.mark.parametrize(
    ("side", "quantity"),
    [
        (Side.BUY, 0),
        (Side.SELL, -1),
    ],
)
def test_order_rejects_non_positive_quantity(side: Side, quantity: int) -> None:
    with pytest.raises(ValueError, match="Quantity must be positive"):
        make_order("AAPL", side, quantity=quantity)


def test_execute_rejects_non_positive_market_price() -> None:
    broker = Broker(Portfolio(cash=1_000, positions={}))
    order = make_order("AAPL", Side.BUY, quantity=1)

    with pytest.raises(ValueError, match="Price must be positive"):
        execute_order(broker, order, price=0)

    assert broker.portfolio.cash == 1_000
    assert broker.portfolio.positions == {}
    assert broker.trades == []


def test_value_with_multiple_positions() -> None:
    broker = Broker(Portfolio(cash=1_000, positions={}))

    execute_order(broker, make_order("AAPL", Side.BUY, quantity=10), price=20)
    execute_order(broker, make_order("MSFT", Side.BUY, quantity=5), price=40)

    value = broker.portfolio.value({"AAPL": 25, "MSFT": 50})

    assert value == 1_100


def test_portfolio_rejects_negative_cash() -> None:
    with pytest.raises(ValueError, match="Cash must not be negative"):
        Portfolio(cash=-1, positions={})


@pytest.mark.parametrize("quantity", [0, -1])
def test_portfolio_rejects_non_positive_initial_positions(quantity: int) -> None:
    with pytest.raises(ValueError, match="Position quantity must be positive"):
        Portfolio(cash=1_000, positions={"AAPL": quantity})


def test_portfolio_positions_returns_copy() -> None:
    portfolio = Portfolio(cash=1_000, positions={"AAPL": 2})

    positions = portfolio.positions
    positions["AAPL"] = 99

    assert portfolio.positions == {"AAPL": 2}


def test_portfolio_value_rejects_missing_market_price() -> None:
    portfolio = Portfolio(cash=1_000, positions={"AAPL": 2})

    with pytest.raises(ValueError, match="Missing market price for position: AAPL"):
        portfolio.value({})


def test_portfolio_value_rejects_non_positive_market_price() -> None:
    portfolio = Portfolio(cash=1_000, positions={"AAPL": 2})

    with pytest.raises(ValueError, match="Market price must be positive"):
        portfolio.value({"AAPL": 0})


def test_order_rejects_empty_symbol() -> None:
    with pytest.raises(ValueError, match="Symbol must be a non-empty string"):
        make_order("", Side.BUY, quantity=1)


def test_trade_rejects_non_positive_price() -> None:
    with pytest.raises(ValueError, match="Price must be positive"):
        Trade("AAPL", Side.BUY, quantity=1, price=0, timestamp=EXECUTION_TIMESTAMP)
