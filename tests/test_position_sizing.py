import pytest

from backtester.portfolio.position_sizing import (
    AllInAllOutSizer,
    FixedSizer,
    PercentSizer,
    SizingContext,
)
from backtester.portfolio.trade import Side


def make_context(
    *,
    cash: float = 1_000,
    current_quantity: int = 10,
    portfolio_value: float = 1_200,
    price: float = 60,
) -> SizingContext:
    return SizingContext(
        cash=cash,
        current_quantity=current_quantity,
        portfolio_value=portfolio_value,
        price=price,
    )


def test_sizing_context_accepts_valid_values() -> None:
    context = make_context()

    assert context == SizingContext(
        cash=1_000,
        current_quantity=10,
        portfolio_value=1_200,
        price=60,
    )


def test_sizing_context_accepts_zero_cash_and_quantity() -> None:
    context = make_context(cash=0, current_quantity=0, portfolio_value=0)

    assert context.cash == 0
    assert context.current_quantity == 0


def test_sizing_context_rejects_negative_cash() -> None:
    with pytest.raises(ValueError, match="cash cannot be negative"):
        make_context(cash=-1)


def test_sizing_context_rejects_negative_current_quantity() -> None:
    with pytest.raises(ValueError, match="current quantity cannot be negative"):
        make_context(current_quantity=-1)


def test_sizing_context_rejects_portfolio_value_below_cash() -> None:
    with pytest.raises(ValueError, match="portfolio value cannot be less than cash"):
        make_context(cash=1_000, portfolio_value=999)


@pytest.mark.parametrize("price", [0, -1])
def test_sizing_context_rejects_non_positive_price(price: float) -> None:
    with pytest.raises(ValueError, match="price must be positive"):
        make_context(price=price)


def test_fixed_sizer_buy_returns_configured_quantity() -> None:
    sizer = FixedSizer(buy_size=7, sell_size=3)

    quantity = sizer.calculate_size(make_context(), Side.BUY)

    assert quantity == 7


def test_fixed_sizer_sell_returns_configured_quantity() -> None:
    sizer = FixedSizer(buy_size=7, sell_size=3)

    quantity = sizer.calculate_size(make_context(), Side.SELL)

    assert quantity == 3


def test_all_in_all_out_buy_uses_all_available_cash_in_whole_shares() -> None:
    sizer = AllInAllOutSizer()

    quantity = sizer.calculate_size(make_context(cash=1_000, price=60), Side.BUY)

    assert quantity == 16


def test_all_in_all_out_buy_returns_zero_when_one_share_is_unaffordable() -> None:
    sizer = AllInAllOutSizer()

    quantity = sizer.calculate_size(make_context(cash=50, price=60), Side.BUY)

    assert quantity == 0


def test_all_in_all_out_sell_uses_the_entire_position() -> None:
    sizer = AllInAllOutSizer()

    quantity = sizer.calculate_size(
        make_context(current_quantity=7),
        Side.SELL,
    )

    assert quantity == 7


@pytest.mark.parametrize(
    ("percent_buy", "percent_sell", "message"),
    [
        (-0.01, 0.5, "percent_buy must be between 0 and 1"),
        (1.01, 0.5, "percent_buy must be between 0 and 1"),
        (0.5, -0.01, "percent_sell must be between 0 and 1"),
        (0.5, 1.01, "percent_sell must be between 0 and 1"),
    ],
)
def test_percent_sizer_rejects_percentages_outside_zero_to_one(
    percent_buy: float,
    percent_sell: float,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        PercentSizer(percent_buy=percent_buy, percent_sell=percent_sell)


def test_percent_sizer_buy_uses_the_configured_cash_percentage() -> None:
    sizer = PercentSizer(percent_buy=0.5, percent_sell=0.25)

    quantity = sizer.calculate_size(make_context(cash=1_000, price=60), Side.BUY)

    assert quantity == 8


def test_percent_sizer_sell_uses_the_configured_position_percentage() -> None:
    sizer = PercentSizer(percent_buy=0.5, percent_sell=0.5)

    quantity = sizer.calculate_size(
        make_context(current_quantity=7),
        Side.SELL,
    )

    assert quantity == 3


@pytest.mark.parametrize(
    ("percent", "expected_buy", "expected_sell"),
    [
        (0.0, 0, 0),
        (1.0, 16, 10),
    ],
)
def test_percent_sizer_accepts_inclusive_percentage_boundaries(
    percent: float,
    expected_buy: int,
    expected_sell: int,
) -> None:
    sizer = PercentSizer(percent_buy=percent, percent_sell=percent)
    context = make_context(cash=1_000, current_quantity=10, price=60)

    assert sizer.calculate_size(context, Side.BUY) == expected_buy
    assert sizer.calculate_size(context, Side.SELL) == expected_sell


def test_position_sizer_rejects_unknown_side() -> None:
    sizer = AllInAllOutSizer()

    with pytest.raises(ValueError, match="Unknown side"):
        sizer.calculate_size(make_context(), None)  # type: ignore[arg-type]
