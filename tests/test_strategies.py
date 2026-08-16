from datetime import datetime, timedelta

import pytest

from backtester.data.models import Candle
from backtester.strategies.base import Signal
from backtester.strategies.mrma import MeanReversionStrategy
from backtester.strategies.moving_average import MovingAverageCrossStrategy
from backtester.strategies.rsi_simple import SimpleRSIStrategy, calculate_simple_rsi


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


@pytest.mark.parametrize("window", [0, -1])
def test_mean_reversion_rejects_non_positive_window(window: int) -> None:
    with pytest.raises(ValueError, match="window must be positive integer"):
        MeanReversionStrategy(window=window, threshold=0.9)


@pytest.mark.parametrize("threshold", [-0.1, 1.1])
def test_mean_reversion_rejects_threshold_outside_zero_to_one(
    threshold: float,
) -> None:
    with pytest.raises(ValueError, match="threshold must be between 0 and 1"):
        MeanReversionStrategy(window=3, threshold=threshold)


def test_mean_reversion_holds_until_enough_candles_for_window() -> None:
    strategy = MeanReversionStrategy(window=3, threshold=0.9)

    signal = strategy.generate_signal(make_candles([100, 100]))

    assert signal is Signal.HOLD


def test_mean_reversion_buys_when_price_is_below_threshold_of_average() -> None:
    strategy = MeanReversionStrategy(window=3, threshold=0.9)

    signal = strategy.generate_signal(make_candles([100, 100, 70]))

    assert signal is Signal.BUY


def test_mean_reversion_sells_when_price_is_at_or_above_average() -> None:
    strategy = MeanReversionStrategy(window=3, threshold=0.9)

    signal = strategy.generate_signal(make_candles([90, 90, 120]))

    assert signal is Signal.SELL


def test_mean_reversion_holds_when_price_is_between_threshold_and_average() -> None:
    strategy = MeanReversionStrategy(window=3, threshold=0.9)

    signal = strategy.generate_signal(make_candles([100, 100, 90]))

    assert signal is Signal.HOLD


@pytest.mark.parametrize("n", [1, 0, -1])
def test_simple_rsi_rejects_periods_smaller_than_two(n: int) -> None:
    with pytest.raises(ValueError, match="n must be greater than 1"):
        SimpleRSIStrategy(n=n)


@pytest.mark.parametrize(
    ("minimum", "maximum"),
    [
        (-1, 70),
        (30, 101),
        (80, 70),
    ],
)
def test_simple_rsi_rejects_invalid_thresholds(
    minimum: float,
    maximum: float,
) -> None:
    with pytest.raises(ValueError, match="0 <= min <= max <= 100"):
        SimpleRSIStrategy(n=3, min=minimum, max=maximum)


def test_calculate_simple_rsi_uses_average_gains_and_losses() -> None:
    rsi = calculate_simple_rsi(3, make_candles([100, 110, 105, 115]))

    assert rsi == pytest.approx(80)


def test_calculate_simple_rsi_returns_100_when_there_are_no_losses() -> None:
    rsi = calculate_simple_rsi(3, make_candles([100, 105, 110, 115]))

    assert rsi == 100


def test_calculate_simple_rsi_returns_0_when_there_are_only_losses() -> None:
    rsi = calculate_simple_rsi(3, make_candles([115, 110, 105, 100]))

    assert rsi == 0


def test_calculate_simple_rsi_uses_only_the_last_n_periods() -> None:
    rsi = calculate_simple_rsi(3, make_candles([1_000, 100, 110, 105, 115]))

    assert rsi == pytest.approx(80)


def test_simple_rsi_holds_until_enough_candles_for_period() -> None:
    strategy = SimpleRSIStrategy(n=3, min=30, max=70)

    signal = strategy.generate_signal(make_candles([100, 95, 90]))

    assert signal is Signal.HOLD


def test_simple_rsi_buys_when_rsi_is_below_minimum_threshold() -> None:
    strategy = SimpleRSIStrategy(n=3, min=30, max=70)

    signal = strategy.generate_signal(make_candles([100, 95, 90, 85]))

    assert signal is Signal.BUY


def test_simple_rsi_sells_when_rsi_is_above_maximum_threshold() -> None:
    strategy = SimpleRSIStrategy(n=3, min=30, max=70)

    signal = strategy.generate_signal(make_candles([100, 105, 110, 115]))

    assert signal is Signal.SELL


def test_simple_rsi_holds_when_rsi_is_between_thresholds() -> None:
    strategy = SimpleRSIStrategy(n=3, min=30, max=70)

    signal = strategy.generate_signal(make_candles([100, 110, 100, 100]))

    assert signal is Signal.HOLD
