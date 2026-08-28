from datetime import datetime, timedelta

import pytest

from backtester.domain.market import Candle
from backtester.domain.trading import Signal
from backtester.strategies.mrma import MeanReversionStrategy


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
