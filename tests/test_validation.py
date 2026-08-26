from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from backtester.data.validation import validate_candles_chronological
from backtester.domain.market import Candle

BASE_CANDLE = Candle(
    timestamp=datetime(2026, 1, 1),
    open=100,
    high=100,
    low=100,
    close=100,
    volume=1_000,
)


def candles_at_offsets(*day_offsets: int) -> list[Candle]:
    return [
        replace(
            BASE_CANDLE,
            timestamp=BASE_CANDLE.timestamp + timedelta(days=day_offset),
        )
        for day_offset in day_offsets
    ]


@pytest.mark.parametrize(
    "candles",
    [[], candles_at_offsets(0), candles_at_offsets(0, 1, 2)],
)
def test_validate_candles_chronological_accepts_strictly_increasing_timestamps(
    candles: list[Candle],
) -> None:
    validate_candles_chronological(candles)


@pytest.mark.parametrize(
    "candles",
    [candles_at_offsets(0, 0), candles_at_offsets(1, 0)],
    ids=["duplicate", "descending"],
)
def test_validate_candles_chronological_rejects_non_increasing_timestamps(
    candles: list[Candle],
) -> None:
    with pytest.raises(ValueError, match="strictly increasing"):
        validate_candles_chronological(candles)


def test_validate_candles_chronological_rejects_incomparable_timestamps() -> None:
    candles = [
        BASE_CANDLE,
        replace(BASE_CANDLE, timestamp=datetime(2026, 1, 2, tzinfo=timezone.utc)),
    ]

    with pytest.raises(ValueError, match="comparable and strictly increasing"):
        validate_candles_chronological(candles)
