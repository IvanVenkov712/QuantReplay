from datetime import datetime
from unittest.mock import Mock

import pytest

from backtester.engine.broker import Broker
from backtester.exceptions.trading_errors import (
    PriceNotFoundError,
    InsufficientFundsError,
    InsufficientPositionError,
)
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


def make_portfolio_mock(cash: float = 1_000, owned_quantity: int = 0) -> Mock:
    portfolio = Mock()
    portfolio.cash = cash
    portfolio.position_quantity.return_value = owned_quantity
    return portfolio


def execute_order(
    broker: Broker,
    order: Order,
    price: float,
    timestamp: datetime = EXECUTION_TIMESTAMP,
) -> None:
    broker.execute(order, prices={order.symbol: price}, timestamp=timestamp)


def test_buy_order_uses_market_price_updates_portfolio_and_records_trade() -> None:
    portfolio = make_portfolio_mock(cash=1_000)
    broker = Broker(portfolio)
    order = make_order("AAPL", Side.BUY, quantity=10)

    execute_order(broker, order, price=20)

    assert portfolio.cash == 800
    portfolio.add_position.assert_called_once_with("AAPL", 10)
    portfolio.remove_position.assert_not_called()
    assert broker.trades == [
        Trade("AAPL", Side.BUY, quantity=10, price=20, timestamp=EXECUTION_TIMESTAMP)
    ]


def test_buy_without_enough_cash_raises_without_updating_portfolio() -> None:
    portfolio = make_portfolio_mock(cash=100)
    broker = Broker(portfolio)
    order = make_order("AAPL", Side.BUY, quantity=6)

    with pytest.raises(InsufficientFundsError):
        execute_order(broker, order, price=20)

    assert portfolio.cash == 100
    portfolio.add_position.assert_not_called()
    portfolio.remove_position.assert_not_called()
    assert broker.trades == []


def test_sell_order_uses_market_price_updates_portfolio_and_records_trade() -> None:
    portfolio = make_portfolio_mock(cash=1_000, owned_quantity=10)
    broker = Broker(portfolio)
    order = make_order("AAPL", Side.SELL, quantity=4)

    execute_order(broker, order, price=25)

    portfolio.position_quantity.assert_called_once_with("AAPL")
    assert portfolio.cash == 1_100
    portfolio.remove_position.assert_called_once_with("AAPL", 4)
    portfolio.add_position.assert_not_called()
    assert broker.trades == [
        Trade("AAPL", Side.SELL, quantity=4, price=25, timestamp=EXECUTION_TIMESTAMP)
    ]


def test_sell_more_shares_than_owned_raises_without_updating_portfolio() -> None:
    portfolio = make_portfolio_mock(cash=1_000, owned_quantity=5)
    broker = Broker(portfolio)
    order = make_order("AAPL", Side.SELL, quantity=6)

    with pytest.raises(InsufficientPositionError):
        execute_order(broker, order, price=25)

    portfolio.position_quantity.assert_called_once_with("AAPL")
    assert portfolio.cash == 1_000
    portfolio.remove_position.assert_not_called()
    portfolio.add_position.assert_not_called()
    assert broker.trades == []


def test_sell_full_position_requests_position_removal() -> None:
    portfolio = make_portfolio_mock(cash=1_000, owned_quantity=5)
    broker = Broker(portfolio)

    execute_order(broker, make_order("AAPL", Side.SELL, quantity=5), price=30)

    assert portfolio.cash == 1_150
    portfolio.remove_position.assert_called_once_with("AAPL", 5)


def test_execute_rejects_missing_market_price_without_updating_portfolio() -> None:
    portfolio = make_portfolio_mock(cash=1_000)
    broker = Broker(portfolio)
    order = make_order("AAPL", Side.BUY, quantity=1)

    with pytest.raises(PriceNotFoundError):
        broker.execute(
            order,
            prices={"MSFT": 20},
            timestamp=EXECUTION_TIMESTAMP,
        )

    assert portfolio.cash == 1_000
    portfolio.add_position.assert_not_called()
    portfolio.remove_position.assert_not_called()
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


def test_execute_rejects_non_positive_market_price_without_trade() -> None:
    portfolio = make_portfolio_mock(cash=1_000)
    broker = Broker(portfolio)
    order = make_order("AAPL", Side.BUY, quantity=1)

    with pytest.raises(ValueError, match="Price must be positive"):
        execute_order(broker, order, price=0)

    assert portfolio.cash == 1_000
    portfolio.add_position.assert_not_called()
    portfolio.remove_position.assert_not_called()
    assert broker.trades == []


def test_trades_returns_copy() -> None:
    broker = Broker(make_portfolio_mock(cash=1_000))
    execute_order(broker, make_order("AAPL", Side.BUY, quantity=1), price=20)

    trades = broker.trades
    trades.clear()

    assert broker.trades == [
        Trade("AAPL", Side.BUY, quantity=1, price=20, timestamp=EXECUTION_TIMESTAMP)
    ]


def test_order_rejects_empty_symbol() -> None:
    with pytest.raises(ValueError, match="Symbol must be a non-empty string"):
        make_order("", Side.BUY, quantity=1)


def test_trade_rejects_non_positive_price() -> None:
    with pytest.raises(ValueError, match="Price must be positive"):
        Trade("AAPL", Side.BUY, quantity=1, price=0, timestamp=EXECUTION_TIMESTAMP)
