"""Convert backtest data into timestamped values for visualization."""

from datetime import datetime
from math import isclose
from typing import Sequence

from backtester.domain.market import Candle
from backtester.domain.trading import Side
from backtester.engine.backtest_result import BacktestResult


def close_price_series(
    candles: Sequence[Candle],
) -> tuple[list[datetime], list[float]]:
    """Return candle timestamps and closing prices in input order."""
    return (
        [candle.timestamp for candle in candles],
        [candle.close for candle in candles]
    )


def equity_series(
    result: BacktestResult,
) -> tuple[list[datetime], list[float]]:
    """Return record timestamps and total portfolio equity in record order."""
    return (
        [record.timestamp for record in result.records],
        [record.snapshot.value for record in result.records]
    )


def cash_series(
    result: BacktestResult,
) -> tuple[list[datetime], list[float]]:
    """Return record timestamps and uninvested portfolio cash in record order."""
    return (
        [record.timestamp for record in result.records],
        [record.snapshot.cash for record in result.records]
    )


def drawdown_series(
    result: BacktestResult,
) -> tuple[list[datetime], list[float]]:
    """Return fractional drawdown from the running peak at each record.

    Drawdown is calculated as ``value / running_peak - 1``. A zero running
    peak produces a drawdown of ``0.0`` because no percentage loss can be
    measured from a zero-valued portfolio.
    """

    if not result.records:
        return [], []
    curr_max = float("-inf")
    drawdowns = []
    timestamps = []
    for r in result.records:
        v = r.snapshot.value
        if v > curr_max:
            curr_max = v
        if isclose(curr_max, 0):
            drawdowns.append(0.0)
        else:
            drawdowns.append(v / curr_max - 1)
        timestamps.append(r.candle.timestamp)

    return timestamps, drawdowns


def trade_marker_series(
    result: BacktestResult,
    side: Side,
) -> tuple[list[datetime], list[float]]:
    """Return fill timestamps and prices for trades matching ``side``."""
    return (
        [trade.timestamp for trade in result.trades if trade.side == side],
        [trade.fill_price for trade in result.trades if trade.side == side],
    )
