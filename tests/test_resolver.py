from collections.abc import Callable
from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from backtester.execution.costs import CommissionModel, ExecutionModel, ExecutionCostCalculator
from backtester.resolving.resolver import (
    BufferQuantityResolver,
    BuyQuantityCapper,
    OrderResolver,
    QuantityResolver,
    ResolutionContext,
)
from backtester.domain.trading import Side, SizingMode, SizingInstruction, Order, OrderIntent

TIMESTAMP = datetime(2024, 1, 2, 9, 30)


def make_context(
    *,
    reference_price: float = 100.0,
    cash: float = 1_000.0,
    current_quantity: int = 10,
    portfolio_value: float = 2_000.0,
) -> ResolutionContext:
    return ResolutionContext(
        timestamp=TIMESTAMP,
        reference_price=reference_price,
        cash=cash,
        current_quantity=current_quantity,
        portfolio_value=portfolio_value,
    )


def make_quantity_resolver(
    *,
    buy_cost: Callable[[int, float], float] | None = None,
    buffer_rate: float | None = None,
) -> QuantityResolver:
    cost_calculator = Mock(spec=ExecutionCostCalculator)
    cost_calculator.estimate_buy_cost.side_effect = (
        buy_cost or (lambda quantity, reference_price: quantity * reference_price)
    )
    capper = BuyQuantityCapper(cost_calculator)
    resolver = QuantityResolver(capper)

    if buffer_rate is None:
        return resolver

    return BufferQuantityResolver(resolver, capper, buffer_rate)


def instruction(mode: SizingMode, value: int | float | None) -> SizingInstruction:
    return SizingInstruction(mode=mode, value=value)


def test_resolution_context_stores_the_portfolio_snapshot() -> None:
    context = make_context()

    assert context == ResolutionContext(
        timestamp=TIMESTAMP,
        reference_price=100.0,
        cash=1_000.0,
        current_quantity=10,
        portfolio_value=2_000.0,
    )


def test_estimate_buy_cost_includes_slippage_and_commission() -> None:
    execution_model = Mock(spec=ExecutionModel)
    execution_model.calculate_fill_price.return_value = 101.0
    commission_model = Mock(spec=CommissionModel)
    commission_model.calculate.return_value = 20.2
    estimator = ExecutionCostCalculator(
        execution_model=execution_model,
        commission_model=commission_model,
    )

    cost = estimator.estimate_buy_cost(quantity=10, reference_price=100.0)

    assert cost == pytest.approx(1_030.2)
    execution_model.calculate_fill_price.assert_called_once_with(100.0, Side.BUY)
    commission_model.calculate.assert_called_once_with(10, 101.0)


def test_estimate_sell_cost_returns_commission_at_the_sell_fill_price() -> None:
    execution_model = Mock(spec=ExecutionModel)
    execution_model.calculate_fill_price.return_value = 99.0
    commission_model = Mock(spec=CommissionModel)
    commission_model.calculate.return_value = 19.8
    estimator = ExecutionCostCalculator(
        execution_model=execution_model,
        commission_model=commission_model,
    )

    cost = estimator.estimate_sell_cost(quantity=10, reference_price=100.0)

    assert cost == pytest.approx(19.8)
    execution_model.calculate_fill_price.assert_called_once_with(100.0, Side.SELL)
    commission_model.calculate.assert_called_once_with(10, 99.0)


def test_all_in_buy_reduces_quantity_until_slippage_and_commission_are_affordable() -> None:
    resolver = make_quantity_resolver(
        buy_cost=lambda quantity, _reference_price: quantity * 101.0 + 1.0,
    )

    quantity = resolver.resolve_quantity(
        Side.BUY,
        instruction(SizingMode.ALL_IN, None),
        make_context(cash=1_000.0, reference_price=100.0),
    )

    assert quantity == 9


def test_all_in_buy_returns_zero_when_one_share_is_unaffordable() -> None:
    resolver = make_quantity_resolver(
        buy_cost=lambda quantity, reference_price: quantity * reference_price + 1.0,
    )

    quantity = resolver.resolve_quantity(
        Side.BUY,
        instruction(SizingMode.ALL_IN, None),
        make_context(cash=100.0, reference_price=100.0),
    )

    assert quantity == 0


@pytest.mark.parametrize("buffer_rate", [-0.01, 1.0, 1.01])
def test_buffer_quantity_resolver_rejects_invalid_buffer_rate(
    buffer_rate: float,
) -> None:
    with pytest.raises(
        ValueError,
        match=r"buffer_rate.*\[0, 1\)",
    ):
        make_quantity_resolver(buffer_rate=buffer_rate)


def test_buffer_quantity_resolver_accepts_zero_as_an_integer() -> None:
    resolver = make_quantity_resolver(buffer_rate=0)

    quantity = resolver.resolve_quantity(
        Side.BUY,
        instruction(SizingMode.ALL_IN, None),
        make_context(cash=1_000.0, reference_price=100.0),
    )

    assert quantity == 10


def test_all_in_buy_reserves_the_configured_cash_buffer() -> None:
    resolver = make_quantity_resolver(buffer_rate=0.25)

    quantity = resolver.resolve_quantity(
        Side.BUY,
        instruction(SizingMode.ALL_IN, None),
        make_context(cash=1_000.0, reference_price=60.0),
    )

    assert quantity == 12


def test_percent_buy_uses_the_requested_fraction_of_available_cash() -> None:
    resolver = make_quantity_resolver()

    quantity = resolver.resolve_quantity(
        Side.BUY,
        instruction(SizingMode.PERCENT, 0.5),
        make_context(cash=1_000.0, reference_price=120.0),
    )

    assert quantity == 4


@pytest.mark.parametrize(
    ("percent", "expected_quantity"),
    [(0.5, 8), (0.9, 12)],
)
def test_percent_buy_uses_the_smaller_of_percent_and_buffer_budgets(
    percent: float,
    expected_quantity: int,
) -> None:
    resolver = make_quantity_resolver(buffer_rate=0.25)

    quantity = resolver.resolve_quantity(
        Side.BUY,
        instruction(SizingMode.PERCENT, percent),
        make_context(cash=1_000.0, reference_price=60.0),
    )

    assert quantity == expected_quantity


def test_up_to_buy_caps_an_otherwise_affordable_quantity() -> None:
    resolver = make_quantity_resolver()

    quantity = resolver.resolve_quantity(
        Side.BUY,
        instruction(SizingMode.UP_TO, 3),
        make_context(cash=1_000.0, reference_price=100.0),
    )

    assert quantity == 3


def test_up_to_buy_still_respects_available_cash() -> None:
    resolver = make_quantity_resolver()

    quantity = resolver.resolve_quantity(
        Side.BUY,
        instruction(SizingMode.UP_TO, 20),
        make_context(cash=450.0, reference_price=100.0),
    )

    assert quantity == 4


def test_fixed_buy_returns_the_requested_quantity_without_affordability_capping() -> None:
    resolver = make_quantity_resolver()

    quantity = resolver.resolve_quantity(
        Side.BUY,
        instruction(SizingMode.FIXED, 12),
        make_context(cash=100.0, reference_price=100.0),
    )

    assert quantity == 12


def test_fixed_buy_is_affordability_capped_when_buffer_is_explicit() -> None:
    resolver = make_quantity_resolver(buffer_rate=0.25)

    quantity = resolver.resolve_quantity(
        Side.BUY,
        instruction(SizingMode.FIXED, 20),
        make_context(cash=1_000.0, reference_price=60.0),
    )

    assert quantity == 12


@pytest.mark.parametrize(
    ("sizing_instruction", "expected_quantity"),
    [
        pytest.param(instruction(SizingMode.FIXED, 12), 12, id="fixed"),
        pytest.param(instruction(SizingMode.ALL_IN, None), 10, id="all-in"),
        pytest.param(instruction(SizingMode.UP_TO, 6), 6, id="up-to-below-position"),
        pytest.param(instruction(SizingMode.UP_TO, 15), 10, id="up-to-above-position"),
        pytest.param(instruction(SizingMode.PERCENT, 0.25), 2, id="percent"),
    ],
)
def test_sell_quantity_resolves_each_sizing_mode(
    sizing_instruction: SizingInstruction,
    expected_quantity: int,
) -> None:
    resolver = make_quantity_resolver()

    quantity = resolver.resolve_quantity(
        Side.SELL,
        sizing_instruction,
        make_context(current_quantity=10),
    )

    assert quantity == expected_quantity


def test_resolve_quantity_rejects_unknown_side() -> None:
    resolver = make_quantity_resolver()

    with pytest.raises(ValueError, match="invalid side"):
        resolver.resolve_quantity(  # type: ignore[arg-type]
            "buy",
            instruction(SizingMode.ALL_IN, None),
            make_context(),
        )


@pytest.mark.parametrize("side", [Side.BUY, Side.SELL])
def test_resolve_quantity_rejects_unknown_sizing_mode(side: Side) -> None:
    resolver = make_quantity_resolver()
    invalid_instruction = Mock(spec=SizingInstruction)
    invalid_instruction.mode = "invalid"

    with pytest.raises(ValueError, match="Invalid sizing instruction"):
        resolver.resolve_quantity(side, invalid_instruction, make_context())


def test_order_resolver_builds_an_order_from_the_resolved_quantity() -> None:
    quantity_resolver = Mock(spec=QuantityResolver)
    quantity_resolver.resolve_quantity.return_value = 7
    resolver = OrderResolver(quantity_resolver)
    sizing_instruction = instruction(SizingMode.FIXED, 7)
    intent = OrderIntent(
        symbol="AAPL",
        side=Side.BUY,
        timestamp=TIMESTAMP - timedelta(days=1),
        sizing_instruction=sizing_instruction,
    )
    context = make_context()

    order = resolver.resolve(intent, context)

    assert order == Order(
        symbol="AAPL",
        side=Side.BUY,
        timestamp=TIMESTAMP,
        quantity=7,
    )
    quantity_resolver.resolve_quantity.assert_called_once_with(
        Side.BUY,
        sizing_instruction,
        context,
    )


@pytest.mark.parametrize("quantity", [0, -1])
def test_order_resolver_returns_none_for_non_positive_quantity(quantity: int) -> None:
    quantity_resolver = Mock(spec=QuantityResolver)
    quantity_resolver.resolve_quantity.return_value = quantity
    resolver = OrderResolver(quantity_resolver)
    intent = OrderIntent(
        symbol="AAPL",
        side=Side.SELL,
        timestamp=TIMESTAMP,
        sizing_instruction=instruction(SizingMode.ALL_IN, None),
    )

    order = resolver.resolve(intent, make_context(current_quantity=0))

    assert order is None
