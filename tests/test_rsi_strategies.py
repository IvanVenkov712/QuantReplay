from datetime import datetime
from unittest.mock import Mock

import pytest

from backtester.domain.market import Candle
from backtester.domain.trading import Signal
from backtester.strategies.calculators import RSICalculator
from backtester.strategies.rsi_strategies import RSIStrategy


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
    rsi_values: list[float | None],
    minimum: float = 30,
    maximum: float = 70,
    window_size: int = 14,
) -> tuple[RSIStrategy, Mock, Mock]:
    calculator = Mock(spec=RSICalculator)
    calculator.next_value.side_effect = rsi_values
    factory = Mock(return_value=calculator)

    strategy = RSIStrategy(
        factory,
        min=minimum,
        max=maximum,
        window_size=window_size,
    )

    return strategy, factory, calculator


@pytest.mark.parametrize(
    ("minimum", "maximum"),
    [
        (-1, 70),
        (30, 101),
        (80, 70),
    ],
)
def test_rsi_strategy_rejects_invalid_thresholds_before_using_factory(
    minimum: float,
    maximum: float,
) -> None:
    factory = Mock()

    with pytest.raises(ValueError, match="0 <= min <= max <= 100"):
        RSIStrategy(factory, min=minimum, max=maximum, window_size=14)

    factory.assert_not_called()


@pytest.mark.parametrize("window_size", [1, 0, -1, 2.5, True, "3", None])
def test_rsi_strategy_rejects_invalid_window_size_before_using_factory(
    window_size: object,
) -> None:
    factory = Mock()

    with pytest.raises(
        ValueError,
        match="positive integer is expected for window size",
    ):
        RSIStrategy(  # type: ignore[arg-type]
            factory,
            min=30,
            max=70,
            window_size=window_size,
        )

    factory.assert_not_called()


def test_rsi_strategy_uses_factory_to_create_calculator() -> None:
    _, factory, _ = make_strategy_with_mocks(
        rsi_values=[],
        window_size=5,
    )

    factory.assert_called_once_with(5)


def test_rsi_strategy_passes_candle_close_to_calculator() -> None:
    strategy, _, calculator = make_strategy_with_mocks(rsi_values=[None])

    signal = strategy.on_candle(make_candle(123.45))

    assert signal is Signal.HOLD
    calculator.next_value.assert_called_once_with(123.45)


@pytest.mark.parametrize(
    ("rsi", "expected_signal"),
    [
        (0.0, Signal.BUY),
        (29.9, Signal.BUY),
        (30.0, Signal.HOLD),
        (50.0, Signal.HOLD),
        (70.0, Signal.HOLD),
        (70.1, Signal.SELL),
        (100.0, Signal.SELL),
    ],
)
def test_rsi_strategy_generates_signal_from_mocked_rsi(
    rsi: float,
    expected_signal: Signal,
) -> None:
    strategy, _, _ = make_strategy_with_mocks(rsi_values=[rsi])

    assert strategy.on_candle(make_candle(100)) is expected_signal


def test_rsi_strategy_reset_resets_factory_created_calculator() -> None:
    strategy, factory, calculator = make_strategy_with_mocks(rsi_values=[])

    strategy.reset()

    calculator.reset.assert_called_once_with()
    factory.assert_called_once_with(14)
