from datetime import datetime
from typing import Sequence

from backtester.domain.market import Candle
from backtester.domain.trading import Side
from backtester.engine.backtest_result import BacktestResult


def close_price_series(
    candles: Sequence[Candle],
) -> tuple[list[datetime], list[float]]:
    return (
        [candle.timestamp for candle in candles],
        [candle.close for candle in candles]
    )


def equity_series(
    result: BacktestResult,
) -> tuple[list[datetime], list[float]]:
    return (
        [record.timestamp for record in result.records],
        [record.snapshot.value for record in result.records]
    )


def cash_series(
    result: BacktestResult,
) -> tuple[list[datetime], list[float]]:
    return (
        [record.timestamp for record in result.records],
        [record.snapshot.cash for record in result.records]
    )


def drawdown_series(
    result: BacktestResult,
) -> tuple[list[datetime], list[float]]:
    ...


def trade_marker_series(
    result: BacktestResult,
    side: Side,
) -> tuple[list[datetime], list[float]]:
    ...