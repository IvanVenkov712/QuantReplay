from datetime import datetime
from unittest.mock import Mock, call

import pytest

from backtester.domain.market import Candle
from backtester.domain.trading import Signal
from backtester.strategies.calculators import MovingAverageCalculator
from backtester.strategies.moving_average import MovingAverageCrossStrategy


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
    long_averages: list[float | None],
    short_averages: list[float | None],
) -> tuple[MovingAverageCrossStrategy, Mock, Mock, Mock]:
    long_calculator = Mock(spec=MovingAverageCalculator)
    short_calculator = Mock(spec=MovingAverageCalculator)
    long_calculator.next_value.side_effect = long_averages
    short_calculator.next_value.side_effect = short_averages
    factory = Mock(side_effect=[long_calculator, short_calculator])

    strategy = MovingAverageCrossStrategy(
        factory,
        short_window_size=2,
        long_window_size=3,
    )

    return strategy, factory, long_calculator, short_calculator


@pytest.mark.parametrize(
    ("short_window_size", "long_window_size"),
    [
        (0, 3),
        (-1, 3),
        (2, 0),
        (2, -1),
    ],
)
def test_moving_average_cross_rejects_non_positive_windows_before_using_factory(
    short_window_size: int,
    long_window_size: int,
) -> None:
    factory = Mock()

    with pytest.raises(ValueError, match="Window sizes must be positive"):
        MovingAverageCrossStrategy(
            factory,
            short_window_size=short_window_size,
            long_window_size=long_window_size,
        )

    factory.assert_not_called()


@pytest.mark.parametrize(
    ("short_window_size", "long_window_size"),
    [(3, 3), (4, 3)],
)
def test_moving_average_cross_requires_short_window_smaller_than_long_window(
    short_window_size: int,
    long_window_size: int,
) -> None:
    factory = Mock()

    with pytest.raises(
        ValueError,
        match="short_window must be smaller than long_window",
    ):
        MovingAverageCrossStrategy(
            factory,
            short_window_size=short_window_size,
            long_window_size=long_window_size,
        )

    factory.assert_not_called()


def test_moving_average_cross_uses_factory_for_long_then_short_calculator() -> None:
    _, factory, _, _ = make_strategy_with_mocks(
        long_averages=[],
        short_averages=[],
    )

    assert factory.call_args_list == [call(3), call(2)]


def test_moving_average_cross_passes_candle_close_to_both_calculators() -> None:
    strategy, _, long_calculator, short_calculator = make_strategy_with_mocks(
        long_averages=[None],
        short_averages=[None],
    )

    signal = strategy.on_candle(make_candle(123.45))

    assert signal is Signal.HOLD
    long_calculator.next_value.assert_called_once_with(123.45)
    short_calculator.next_value.assert_called_once_with(123.45)


@pytest.mark.parametrize(
    ("first_long_average", "first_short_average"),
    [(None, 9.0), (10.0, None)],
)
def test_moving_average_cross_waits_for_both_averages_before_storing_baseline(
    first_long_average: float | None,
    first_short_average: float | None,
) -> None:
    strategy, _, _, _ = make_strategy_with_mocks(
        long_averages=[first_long_average, 10.0],
        short_averages=[first_short_average, 11.0],
    )

    assert strategy.on_candle(make_candle(100)) is Signal.HOLD
    assert strategy.on_candle(make_candle(101)) is Signal.HOLD


def test_moving_average_cross_holds_when_first_complete_averages_set_baseline() -> None:
    strategy, _, _, _ = make_strategy_with_mocks(
        long_averages=[10.0],
        short_averages=[11.0],
    )

    assert strategy.on_candle(make_candle(100)) is Signal.HOLD


@pytest.mark.parametrize("previous_short_average", [9.0, 10.0])
def test_moving_average_cross_buys_when_short_average_crosses_above_long(
    previous_short_average: float,
) -> None:
    strategy, _, _, _ = make_strategy_with_mocks(
        long_averages=[10.0, 10.0],
        short_averages=[previous_short_average, 11.0],
    )

    assert strategy.on_candle(make_candle(100)) is Signal.HOLD
    assert strategy.on_candle(make_candle(101)) is Signal.BUY


@pytest.mark.parametrize("previous_short_average", [11.0, 10.0])
def test_moving_average_cross_sells_when_short_average_crosses_below_long(
    previous_short_average: float,
) -> None:
    strategy, _, _, _ = make_strategy_with_mocks(
        long_averages=[10.0, 10.0],
        short_averages=[previous_short_average, 9.0],
    )

    assert strategy.on_candle(make_candle(100)) is Signal.HOLD
    assert strategy.on_candle(make_candle(99)) is Signal.SELL


@pytest.mark.parametrize(
    ("previous_short_average", "current_short_average"),
    [(9.0, 8.0), (11.0, 12.0), (10.0, 10.0)],
)
def test_moving_average_cross_holds_when_averages_do_not_cross(
    previous_short_average: float,
    current_short_average: float,
) -> None:
    strategy, _, _, _ = make_strategy_with_mocks(
        long_averages=[10.0, 10.0],
        short_averages=[previous_short_average, current_short_average],
    )

    strategy.on_candle(make_candle(100))

    assert strategy.on_candle(make_candle(101)) is Signal.HOLD


def test_moving_average_cross_reset_clears_calculators_and_crossover_baseline() -> None:
    strategy, factory, long_calculator, short_calculator = make_strategy_with_mocks(
        long_averages=[10.0, 10.0, 10.0],
        short_averages=[9.0, 11.0, 9.0],
    )
    strategy.on_candle(make_candle(100))

    strategy.reset()

    long_calculator.reset.assert_called_once_with()
    short_calculator.reset.assert_called_once_with()
    assert factory.call_count == 2
    assert strategy.on_candle(make_candle(101)) is Signal.HOLD
    assert strategy.on_candle(make_candle(102)) is Signal.SELL
