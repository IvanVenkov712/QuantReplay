from datetime import datetime
from unittest.mock import Mock

import pytest

from backtester.domain.market import Candle
from backtester.domain.trading import Signal
from backtester.strategies.calculators import MovingAverageCalculator
from backtester.strategies.mrma import MeanReversionStrategy


def make_candle(close: float) -> Candle:
    return Candle(
        timestamp=datetime(2026, 1, 1),
        open=close,
        high=close,
        low=close,
        close=close,
        volume=1_000,
    )


def make_strategy_with_mocks(
    *,
    averages: list[float | None],
    window: int = 3,
    threshold: float = 0.9,
) -> tuple[MeanReversionStrategy, Mock, Mock]:
    calculator = Mock(spec=MovingAverageCalculator)
    calculator.next_value.side_effect = averages
    factory = Mock(return_value=calculator)

    strategy = MeanReversionStrategy(
        window=window,
        threshold=threshold,
        factory=factory,
    )

    return strategy, factory, calculator


@pytest.mark.parametrize("window", [0, -1])
def test_mean_reversion_rejects_non_positive_window_before_using_factory(
    window: int,
) -> None:
    factory = Mock()

    with pytest.raises(ValueError, match="window must be positive integer"):
        MeanReversionStrategy(window=window, threshold=0.9, factory=factory)

    factory.assert_not_called()


@pytest.mark.parametrize("threshold", [-0.1, 1.1])
def test_mean_reversion_rejects_threshold_outside_zero_to_one_before_using_factory(
    threshold: float,
) -> None:
    factory = Mock()

    with pytest.raises(ValueError, match="threshold must be between 0 and 1"):
        MeanReversionStrategy(window=3, threshold=threshold, factory=factory)

    factory.assert_not_called()


def test_mean_reversion_uses_factory_to_create_calculator() -> None:
    _, factory, _ = make_strategy_with_mocks(averages=[], window=5)

    factory.assert_called_once_with(5)


def test_mean_reversion_passes_candle_close_to_calculator() -> None:
    strategy, _, calculator = make_strategy_with_mocks(averages=[None])

    signal = strategy.on_candle(make_candle(123.45))

    assert signal is Signal.HOLD
    calculator.next_value.assert_called_once_with(123.45)


@pytest.mark.parametrize(
    ("price", "average", "expected_signal"),
    [
        (89.99, 100.0, Signal.BUY),
        (90.0, 100.0, Signal.HOLD),
        (99.99, 100.0, Signal.HOLD),
        (100.0, 100.0, Signal.SELL),
        (100.01, 100.0, Signal.SELL),
    ],
)
def test_mean_reversion_generates_signal_from_mocked_average(
    price: float,
    average: float,
    expected_signal: Signal,
) -> None:
    strategy, _, _ = make_strategy_with_mocks(averages=[average])

    assert strategy.on_candle(make_candle(price)) is expected_signal


def test_mean_reversion_holds_when_calculator_has_no_average() -> None:
    strategy, _, _ = make_strategy_with_mocks(averages=[None])

    assert strategy.on_candle(make_candle(100)) is Signal.HOLD


def test_mean_reversion_reset_resets_factory_created_calculator() -> None:
    strategy, factory, calculator = make_strategy_with_mocks(averages=[])

    strategy.reset()

    calculator.reset.assert_called_once_with()
    factory.assert_called_once_with(3)
