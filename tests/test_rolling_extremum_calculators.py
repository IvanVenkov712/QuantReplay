from unittest.mock import Mock

import pytest

from backtester.strategies.calculators import (
    RollingExtremumCalculator,
    RollingMaxCalculator,
    RollingMinCalculator,
)


@pytest.mark.parametrize("window_size", [0, -1, 2.5, True, False, "3", None])
def test_rolling_extremum_rejects_invalid_window_size(window_size: object) -> None:
    key = Mock()

    with pytest.raises(ValueError, match="Positive integer expected for window_size"):
        RollingExtremumCalculator(window_size, key)  # type: ignore[arg-type]

    key.assert_not_called()


@pytest.mark.parametrize("calculator_type", [RollingMaxCalculator, RollingMinCalculator])
def test_window_of_one_returns_each_current_value(
    calculator_type: type[RollingExtremumCalculator],
) -> None:
    calculator = calculator_type(window_size=1)

    assert [calculator.next_value(value) for value in [2.5, -1.5, 0, 0]] == [
        2.5, -1.5, 0, 0,
    ]


@pytest.mark.parametrize(
    ("calculator_type", "values", "expected"),
    [
        (RollingMaxCalculator, [1, 2, 3, 4, 5], [None, None, 3, 4, 5]),
        (RollingMaxCalculator, [5, 4, 3, 2, 1], [None, None, 5, 4, 3]),
        (RollingMinCalculator, [1, 2, 3, 4, 5], [None, None, 1, 2, 3]),
        (RollingMinCalculator, [5, 4, 3, 2, 1], [None, None, 3, 2, 1]),
        (RollingMaxCalculator, [5, 1, 4, 2, 6, 0], [None, None, 5, 4, 6, 6]),
        (RollingMinCalculator, [1, 5, 2, 4, 0, 6], [None, None, 1, 2, 0, 0]),
        (RollingMaxCalculator, [5, 5, 1, 2, 0], [None, None, 5, 5, 2]),
        (RollingMinCalculator, [1, 1, 5, 4, 6], [None, None, 1, 1, 4]),
        (RollingMaxCalculator, [2, 2, 2, 2], [None, None, 2, 2]),
        (RollingMinCalculator, [2, 2, 2, 2], [None, None, 2, 2]),
        (RollingMaxCalculator, [-2.5, -1.5, -3.5, 0], [None, None, -1.5, 0]),
        (RollingMinCalculator, [-2.5, -1.5, -3.5, 0], [None, None, -3.5, -3.5]),
    ],
    ids=[
        "max-increasing", "max-decreasing", "min-increasing", "min-decreasing",
        "max-mixed", "min-mixed", "max-duplicate-expires", "min-duplicate-expires",
        "max-constant", "min-constant", "max-negative-fractions", "min-negative-fractions",
    ],
)
def test_rolling_extremum_uses_latest_full_window(
    calculator_type: type[RollingExtremumCalculator],
    values: list[float],
    expected: list[float | None],
) -> None:
    calculator = calculator_type(window_size=3)

    assert [calculator.next_value(value) for value in values] == expected


def test_custom_key_selects_original_value_with_largest_key() -> None:
    key = Mock(side_effect=abs)
    calculator = RollingExtremumCalculator(window_size=2, key=key)

    assert calculator.next_value(-4) is None
    assert calculator.next_value(2) == -4
    assert calculator.next_value(-3) == -3
    assert calculator.next_value(5) == 5


@pytest.mark.parametrize("calculator_type", [RollingMaxCalculator, RollingMinCalculator])
@pytest.mark.parametrize("previous_values", [[], [100], [100, -100, 50, -50]])
def test_reset_discards_values_and_restarts_warmup(
    calculator_type: type[RollingExtremumCalculator],
    previous_values: list[float],
) -> None:
    calculator = calculator_type(window_size=3)
    for value in previous_values:
        calculator.next_value(value)

    calculator.reset()
    calculator.reset()

    assert calculator.next_value(7) is None
    assert calculator.next_value(7) is None
    assert calculator.next_value(7) == 7


def test_reset_preserves_custom_key() -> None:
    calculator = RollingExtremumCalculator(window_size=2, key=Mock(side_effect=abs))
    calculator.next_value(100)
    calculator.next_value(-200)

    calculator.reset()

    assert calculator.next_value(-4) is None
    assert calculator.next_value(2) == -4
