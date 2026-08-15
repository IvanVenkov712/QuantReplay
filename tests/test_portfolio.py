import pytest

from src.backtester.portfolio.portfolio import Portfolio


def test_buy_updates_cash_and_position() -> None:
    portfolio = Portfolio(cash=1_000)

    portfolio.buy("AAPL", quantity=10, price=20)

    assert portfolio.cash == 800
    assert portfolio.positions == {"AAPL": 10}


def test_buy_without_enough_cash_raises_and_keeps_state() -> None:
    portfolio = Portfolio(cash=100)

    with pytest.raises(ValueError, match="Insufficient cash"):
        portfolio.buy("AAPL", quantity=6, price=20)

    assert portfolio.cash == 100
    assert portfolio.positions == {}


def test_sell_updates_cash_and_reduces_position() -> None:
    portfolio = Portfolio(cash=1_000)
    portfolio.buy("AAPL", quantity=10, price=20)

    portfolio.sell("AAPL", quantity=4, price=25)

    assert portfolio.cash == 900
    assert portfolio.positions == {"AAPL": 6}


def test_sell_more_shares_than_owned_raises_and_keeps_state() -> None:
    portfolio = Portfolio(cash=1_000)
    portfolio.buy("AAPL", quantity=5, price=20)

    with pytest.raises(ValueError, match="Insufficient position"):
        portfolio.sell("AAPL", quantity=6, price=25)

    assert portfolio.cash == 900
    assert portfolio.positions == {"AAPL": 5}


def test_sell_full_position_removes_symbol() -> None:
    portfolio = Portfolio(cash=1_000)
    portfolio.buy("AAPL", quantity=5, price=20)

    portfolio.sell("AAPL", quantity=5, price=30)

    assert portfolio.cash == 1_050
    assert portfolio.positions == {}


def test_value_with_multiple_positions() -> None:
    portfolio = Portfolio(cash=1_000)
    portfolio.buy("AAPL", quantity=10, price=20)
    portfolio.buy("MSFT", quantity=5, price=40)

    value = portfolio.value({"AAPL": 25, "MSFT": 50})

    assert value == 1_100
