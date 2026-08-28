from collections.abc import Callable

import pytest

from backtester.strategies.calculators import (
    ExponentialMovingAverageCalculator,
    SimpleMovingAverageCalculator,
)


@pytest.mark.parametrize("window_size", [0, -1, 2.5, True, "3", None])
def test_simple_moving_average_rejects_invalid_window_size(
    window_size: object,
) -> None:
    with pytest.raises(
        ValueError,
        match="positive integer is expected for window size",
    ):
        SimpleMovingAverageCalculator(window_size)  # type: ignore[arg-type]


def test_simple_moving_average_exposes_window_size() -> None:
    calculator = SimpleMovingAverageCalculator(window_size=3)

    assert calculator.window_size == 3


def test_simple_moving_average_with_window_of_one_returns_first_value() -> None:
    calculator = SimpleMovingAverageCalculator(window_size=1)

    assert calculator.next_value(12.5) == 12.5


def test_simple_moving_average_waits_for_full_window_and_uses_latest_values() -> None:
    calculator = SimpleMovingAverageCalculator(window_size=3)

    assert calculator.next_value(10) is None
    assert calculator.next_value(20) is None
    assert calculator.next_value(30) == pytest.approx(20)
    assert calculator.next_value(50) == pytest.approx(100 / 3)


def test_simple_moving_average_reset_discards_accumulated_values() -> None:
    calculator = SimpleMovingAverageCalculator(window_size=2)
    calculator.next_value(10)
    assert calculator.next_value(20) == pytest.approx(15)

    calculator.reset()

    assert calculator.next_value(100) is None
    assert calculator.next_value(300) == pytest.approx(200)


@pytest.mark.parametrize("window_size", [0, -1, 2.5, True, "3", None])
def test_exponential_moving_average_rejects_invalid_window_size(
    window_size: object,
) -> None:
    with pytest.raises(
        ValueError,
        match="positive integer is expected for window size",
    ):
        ExponentialMovingAverageCalculator(  # type: ignore[arg-type]
            window_size,
            alpha=0.5,
        )


@pytest.mark.parametrize("alpha", [0, 1, -0.1, 1.1])
def test_exponential_moving_average_rejects_alpha_outside_open_unit_interval(
    alpha: float,
) -> None:
    with pytest.raises(ValueError, match=r"alpha must be in \(0, 1\)"):
        ExponentialMovingAverageCalculator(window_size=3, alpha=alpha)


def test_exponential_moving_average_uses_simple_average_as_initial_value() -> None:
    calculator = ExponentialMovingAverageCalculator(window_size=3, alpha=0.5)

    assert calculator.next_value(10) is None
    assert calculator.next_value(20) is None
    assert calculator.next_value(40) == pytest.approx(70 / 3)


def test_exponential_moving_average_applies_alpha_after_initial_window() -> None:
    calculator = ExponentialMovingAverageCalculator(window_size=3, alpha=0.5)
    calculator.next_value(10)
    calculator.next_value(20)
    calculator.next_value(40)

    assert calculator.next_value(50) == pytest.approx(110 / 3)
    assert calculator.next_value(30) == pytest.approx(100 / 3)


def test_exponential_moving_average_reset_discards_accumulated_state() -> None:
    calculator = ExponentialMovingAverageCalculator(window_size=2, alpha=0.5)
    calculator.next_value(10)
    calculator.next_value(20)
    assert calculator.next_value(30) == pytest.approx(22.5)

    calculator.reset()

    assert calculator.next_value(100) is None
    assert calculator.next_value(300) == pytest.approx(200)
    assert calculator.next_value(100) == pytest.approx(150)


@pytest.mark.parametrize(
    "factory",
    [
        ExponentialMovingAverageCalculator.standard,
        ExponentialMovingAverageCalculator.wilder,
    ],
)
@pytest.mark.parametrize("window_size", [1, 0, -1, 2.5, True])
def test_exponential_moving_average_factories_reject_invalid_window_size(
    factory: Callable[[int], ExponentialMovingAverageCalculator],
    window_size: object,
) -> None:
    with pytest.raises(ValueError, match="integer > 1 is expected for window size"):
        factory(window_size)  # type: ignore[arg-type]


def test_standard_exponential_moving_average_uses_standard_alpha() -> None:
    calculator = ExponentialMovingAverageCalculator.standard(3)
    calculator.next_value(10)
    calculator.next_value(20)
    calculator.next_value(30)

    assert calculator.next_value(50) == pytest.approx(35)


def test_wilder_exponential_moving_average_uses_wilder_alpha() -> None:
    calculator = ExponentialMovingAverageCalculator.wilder(4)
    calculator.next_value(10)
    calculator.next_value(20)
    calculator.next_value(30)
    calculator.next_value(40)

    assert calculator.next_value(45) == pytest.approx(30)
