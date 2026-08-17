import pytest

from backtester.portfolio.portfolio import Portfolio


def test_value_with_multiple_positions() -> None:
    portfolio = Portfolio(cash=600, positions={"AAPL": 10, "MSFT": 5})

    value = portfolio.value({"AAPL": 25, "MSFT": 50})

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
