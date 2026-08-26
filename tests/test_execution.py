import pytest

from backtester.execution.costs import ExecutionModel
from backtester.domain.trading import Side


@pytest.mark.parametrize(
    ("side", "expected_fill_price"),
    [
        (Side.BUY, 101.0),
        (Side.SELL, 99.0),
    ],
)
def test_calculate_fill_price_applies_slippage_against_trader(
    side: Side,
    expected_fill_price: float,
) -> None:
    execution_model = ExecutionModel(slippage_rate=0.01)

    fill_price = execution_model.calculate_fill_price(
        reference_price=100.0,
        side=side,
    )

    assert fill_price == pytest.approx(expected_fill_price)


@pytest.mark.parametrize("side", [Side.BUY, Side.SELL])
def test_zero_slippage_preserves_reference_price(side: Side) -> None:
    execution_model = ExecutionModel(slippage_rate=0.0)

    fill_price = execution_model.calculate_fill_price(
        reference_price=123.45,
        side=side,
    )

    assert fill_price == pytest.approx(123.45)


@pytest.mark.parametrize("slippage_rate", [-0.01, 1.0, 1.01])
def test_execution_model_rejects_slippage_rate_outside_valid_range(
    slippage_rate: float,
) -> None:
    with pytest.raises(ValueError, match=r"slippage_rate must be in \[0, 1\)"):
        ExecutionModel(slippage_rate=slippage_rate)


@pytest.mark.parametrize("reference_price", [0.0, -100.0])
def test_calculate_fill_price_rejects_non_positive_reference_price(
    reference_price: float,
) -> None:
    execution_model = ExecutionModel(slippage_rate=0.01)

    with pytest.raises(ValueError, match="reference_price must be positive"):
        execution_model.calculate_fill_price(
            reference_price=reference_price,
            side=Side.BUY,
        )


def test_calculate_fill_price_rejects_unknown_side() -> None:
    execution_model = ExecutionModel(slippage_rate=0.01)

    with pytest.raises(ValueError, match="Unknown side"):
        execution_model.calculate_fill_price(  # type: ignore[arg-type]
            reference_price=100.0,
            side="buy",
        )
