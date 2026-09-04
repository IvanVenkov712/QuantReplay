from datetime import datetime, timedelta

import pytest

from backtester.domain.market import Candle
from backtester.domain.trading import Signal
from backtester.strategies.breakout import DonchianBreakoutStrategy


def make_candle(
    *,
    high: float,
    low: float,
    close: float,
    day: int = 0,
) -> Candle:
    return Candle(
        timestamp=datetime(2026, 1, 1) + timedelta(days=day),
        open=close,
        high=high,
        low=low,
        close=close,
        volume=1_000,
    )


@pytest.mark.parametrize(
    ("entry_window", "exit_window", "message"),
    [
        (0, 10, "Positive integer expected for entry_window"),
        (-1, 10, "Positive integer expected for entry_window"),
        (20, 0, "Positive integer expected for exit_window"),
        (20, -1, "Positive integer expected for exit_window"),
    ],
)
def test_donchian_breakout_rejects_non_positive_windows(
    entry_window: int,
    exit_window: int,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        DonchianBreakoutStrategy(
            entry_window=entry_window,
            exit_window=exit_window,
        )


def test_donchian_breakout_holds_until_both_channels_are_full() -> None:
    strategy = DonchianBreakoutStrategy(entry_window=3, exit_window=2)

    signals = [
        strategy.on_candle(make_candle(high=10, low=8, close=9, day=0)),
        strategy.on_candle(make_candle(high=11, low=9, close=10, day=1)),
        strategy.on_candle(make_candle(high=20, low=10, close=20, day=2)),
    ]

    assert signals == [Signal.HOLD, Signal.HOLD, Signal.HOLD]


def test_donchian_breakout_buys_above_prior_entry_channel() -> None:
    strategy = DonchianBreakoutStrategy(entry_window=2, exit_window=2)
    strategy.on_candle(make_candle(high=10, low=8, close=9, day=0))
    strategy.on_candle(make_candle(high=12, low=9, close=11, day=1))

    signal = strategy.on_candle(make_candle(high=13, low=10, close=13, day=2))

    assert signal is Signal.BUY


def test_donchian_breakout_sells_below_prior_exit_channel() -> None:
    strategy = DonchianBreakoutStrategy(entry_window=2, exit_window=2)
    strategy.on_candle(make_candle(high=10, low=8, close=9, day=0))
    strategy.on_candle(make_candle(high=12, low=9, close=11, day=1))

    signal = strategy.on_candle(make_candle(high=9, low=7, close=7, day=2))

    assert signal is Signal.SELL


@pytest.mark.parametrize("close", [8, 12])
def test_donchian_breakout_holds_at_channel_boundary(close: float) -> None:
    strategy = DonchianBreakoutStrategy(entry_window=1, exit_window=1)
    strategy.on_candle(make_candle(high=12, low=8, close=10))

    signal = strategy.on_candle(make_candle(high=12, low=8, close=close))

    assert signal is Signal.HOLD


def test_donchian_breakout_discards_values_outside_rolling_window() -> None:
    strategy = DonchianBreakoutStrategy(entry_window=2, exit_window=2)
    strategy.on_candle(make_candle(high=110, low=80, close=100, day=0))
    strategy.on_candle(make_candle(high=90, low=80, close=85, day=1))

    assert (
        strategy.on_candle(make_candle(high=100, low=80, close=100, day=2))
        is Signal.HOLD
    )
    assert (
        strategy.on_candle(make_candle(high=105, low=80, close=105, day=3))
        is Signal.BUY
    )


def test_donchian_breakout_reset_returns_strategy_to_warm_up() -> None:
    strategy = DonchianBreakoutStrategy(entry_window=1, exit_window=1)
    strategy.on_candle(make_candle(high=10, low=8, close=9, day=0))
    assert (
        strategy.on_candle(make_candle(high=11, low=9, close=11, day=1))
        is Signal.BUY
    )

    strategy.reset()

    assert (
        strategy.on_candle(make_candle(high=20, low=10, close=20, day=2))
        is Signal.HOLD
    )
