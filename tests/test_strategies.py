from datetime import datetime, timedelta

import pytest

from backtester.data.models import Candle
from backtester.strategies.base import Signal
from backtester.strategies.moving_average import MovingAverageCrossStrategy


def make_candles(closes: list[float]) -> list[Candle]:
    start = datetime(2026, 1, 1)

    return [
        Candle(
            timestamp=start + timedelta(days=index),
            open=close,
            high=close,
            low=close,
            close=close,
            volume=1_000,
        )
        for index, close in enumerate(closes)
    ]


@pytest.mark.parametrize(
    ("short_window", "long_window"),
    [
        (0, 3),
        (-1, 3),
        (2, 0),
        (3, -1),
    ],
)
def test_moving_average_rejects_non_positive_windows(
    short_window: int,
    long_window: int,
) -> None:
    with pytest.raises(ValueError, match="Window sizes must be positive"):
        MovingAverageCrossStrategy(short_window=short_window, long_window=long_window)


@pytest.mark.parametrize(
    ("short_window", "long_window"),
    [
        (3, 3),
        (4, 3),
    ],
)
def test_moving_average_requires_short_window_smaller_than_long_window(
    short_window: int,
    long_window: int,
) -> None:
    with pytest.raises(ValueError, match="short_window must be smaller than long_window"):
        MovingAverageCrossStrategy(short_window=short_window, long_window=long_window)


def test_moving_average_holds_until_enough_candles_for_crossover() -> None:
    strategy = MovingAverageCrossStrategy(short_window=2, long_window=3)

    signal = strategy.generate_signal(make_candles([10, 11, 12]))

    assert signal is Signal.HOLD


def test_moving_average_buys_when_short_average_crosses_above_long_average() -> None:
    strategy = MovingAverageCrossStrategy(short_window=2, long_window=3)

    signal = strategy.generate_signal(make_candles([10, 10, 8, 14]))

    assert signal is Signal.BUY


def test_moving_average_sells_when_short_average_crosses_below_long_average() -> None:
    strategy = MovingAverageCrossStrategy(short_window=2, long_window=3)

    signal = strategy.generate_signal(make_candles([10, 10, 12, 6]))

    assert signal is Signal.SELL


def test_moving_average_holds_when_averages_do_not_cross() -> None:
    strategy = MovingAverageCrossStrategy(short_window=2, long_window=3)

    signal = strategy.generate_signal(make_candles([10, 11, 12, 13]))

    assert signal is Signal.HOLD
