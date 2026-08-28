from unittest.mock import Mock, call

import pytest

from backtester.strategies.calculators import (
    MovingAverageCalculator,
    RSICalculator,
)


def make_rsi_with_mocks(
    *,
    average_gain: float | None = None,
    average_loss: float | None = None,
    window_size: int = 3,
) -> tuple[RSICalculator, Mock, Mock, Mock]:
    gain_calculator = Mock(spec=MovingAverageCalculator)
    loss_calculator = Mock(spec=MovingAverageCalculator)
    gain_calculator.next_value.return_value = average_gain
    loss_calculator.next_value.return_value = average_loss
    factory = Mock(side_effect=[gain_calculator, loss_calculator])

    calculator = RSICalculator(factory, window_size=window_size)

    return calculator, factory, gain_calculator, loss_calculator


@pytest.mark.parametrize("window_size", [1, 0, -1, 2.5, True, "3", None])
def test_rsi_rejects_invalid_window_size_before_calling_factory(
    window_size: object,
) -> None:
    factory = Mock()

    with pytest.raises(
        ValueError,
        match="positive integer is expected for window size",
    ):
        RSICalculator(factory, window_size=window_size)  # type: ignore[arg-type]

    factory.assert_not_called()


def test_rsi_uses_factory_to_create_gain_and_loss_calculators() -> None:
    _, factory, _, _ = make_rsi_with_mocks(window_size=5)

    assert factory.call_args_list == [call(5), call(5)]


def test_rsi_first_value_only_initializes_previous_value() -> None:
    calculator, _, gain_calculator, loss_calculator = make_rsi_with_mocks()

    assert calculator.next_value(100) is None
    gain_calculator.next_value.assert_not_called()
    loss_calculator.next_value.assert_not_called()


def test_rsi_passes_upward_and_downward_moves_to_separate_calculators() -> None:
    calculator, _, gain_calculator, loss_calculator = make_rsi_with_mocks()

    calculator.next_value(100)
    calculator.next_value(110)
    calculator.next_value(105)

    assert gain_calculator.next_value.call_args_list == [call(10), call(0)]
    assert loss_calculator.next_value.call_args_list == [call(0), call(5)]


@pytest.mark.parametrize(
    ("average_gain", "average_loss"),
    [(None, 1.0), (1.0, None)],
)
def test_rsi_returns_none_until_both_averages_are_available(
    average_gain: float | None,
    average_loss: float | None,
) -> None:
    calculator, _, _, _ = make_rsi_with_mocks(
        average_gain=average_gain,
        average_loss=average_loss,
    )
    calculator.next_value(100)

    assert calculator.next_value(105) is None


@pytest.mark.parametrize(
    ("average_gain", "average_loss", "expected_rsi"),
    [
        (4.0, 1.0, 80.0),
        (1.0, 1.0, 50.0),
        (0.0, 2.0, 0.0),
    ],
)
def test_rsi_calculates_value_from_mocked_averages(
    average_gain: float,
    average_loss: float,
    expected_rsi: float,
) -> None:
    calculator, _, _, _ = make_rsi_with_mocks(
        average_gain=average_gain,
        average_loss=average_loss,
    )
    calculator.next_value(100)

    assert calculator.next_value(105) == pytest.approx(expected_rsi)


@pytest.mark.parametrize(
    ("average_gain", "expected_rsi"),
    [(0.0, 50.0), (3.0, 100.0)],
)
def test_rsi_handles_zero_average_loss(
    average_gain: float,
    expected_rsi: float,
) -> None:
    calculator, _, _, _ = make_rsi_with_mocks(
        average_gain=average_gain,
        average_loss=0.0,
    )
    calculator.next_value(100)

    assert calculator.next_value(105) == expected_rsi


def test_rsi_reset_resets_both_calculators_and_previous_value() -> None:
    calculator, factory, gain_calculator, loss_calculator = make_rsi_with_mocks()
    calculator.next_value(100)
    calculator.next_value(110)

    calculator.reset()

    gain_calculator.reset.assert_called_once_with()
    loss_calculator.reset.assert_called_once_with()
    assert factory.call_count == 2

    gain_calculator.next_value.reset_mock()
    loss_calculator.next_value.reset_mock()
    assert calculator.next_value(200) is None
    gain_calculator.next_value.assert_not_called()
    loss_calculator.next_value.assert_not_called()
