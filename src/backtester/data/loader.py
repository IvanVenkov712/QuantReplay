"""Load, normalize, validate, and convert historical OHLCV data."""

from abc import ABC, abstractmethod
from datetime import date
from math import isfinite
from pathlib import Path

import pandas as pd
import yfinance as yf
from pandas import DataFrame

from backtester.domain.market import Candle

REQUIRED_OHLCV_COLUMNS = ("open", "high", "low", "close", "volume")
TIMESTAMP_COLUMNS = ("timestamp", "date", "datetime")
YFINANCE_INTERVAL = "1d"


class DataSource(ABC):
    """Interface for loading normalized historical OHLCV data."""

    @abstractmethod
    def load(self, symbol: str, start: str, end: str) -> DataFrame | None:
        """Load one symbol for an inclusive start and exclusive end date."""


class YFinanceDataSource(DataSource):
    """Load adjusted daily OHLCV data from Yahoo Finance."""

    def load(self, symbol: str, start: str, end: str) -> DataFrame | None:
        """Download and normalize adjusted daily candles for one symbol."""
        start_timestamp, end_timestamp = parse_date_range(start, end)

        data = yf.download(
            tickers=symbol,
            start=start,
            end=end,
            interval=YFINANCE_INTERVAL,
            auto_adjust=True,
            progress=False,
            multi_level_index=False,
        )

        if data is None:
            return None

        return prepare_market_data(
            normalize_yfinance_data(data, symbol),
            "date",
            start_timestamp,
            end_timestamp,
        )


class CSVDataSource(DataSource):
    """Load OHLCV data from one CSV file or a directory of symbol files."""

    def __init__(self, path: Path):
        self.__path: Path = path

    def load(self, symbol: str, start: str, end: str) -> DataFrame | None:
        """Load and normalize one symbol over the requested half-open range."""
        start_timestamp, end_timestamp = parse_date_range(start, end)
        data = self.__read_symbol_data(symbol)

        return prepare_market_data(
            data,
            find_timestamp_column(data),
            start_timestamp,
            end_timestamp,
        )

    def first_available_date(self, symbol: str) -> date:
        """Return the earliest CSV candle date available for one symbol."""
        data = self.__read_symbol_data(symbol)
        if data.empty:
            raise ValueError(f"CSV data contains no rows for symbol: {symbol}.")

        timestamp_column = find_timestamp_column(data)
        timestamps = pd.to_datetime(data[timestamp_column], errors="raise")
        first_timestamp = timestamps.min()
        if pd.isna(first_timestamp):
            raise ValueError("CSV data must contain at least one valid timestamp.")

        return first_timestamp.date()

    def __read_symbol_data(self, symbol: str) -> DataFrame:
        data = normalize_column_names(pd.read_csv(self.__resolve_csv_path(symbol)))
        if "symbol" in data.columns:
            data = data.loc[data["symbol"] == symbol].copy()
        return data

    def __resolve_csv_path(self, symbol: str) -> Path:
        if self.__path.is_dir():
            return self.__path / f"{symbol}.csv"

        return self.__path


def normalize_yfinance_data(data: DataFrame, symbol: str) -> DataFrame:
    """Flatten a Yahoo Finance frame and normalize its date column name."""
    normalized = normalize_column_names(select_symbol_columns(data, symbol).reset_index())
    return normalized.rename(columns={"datetime": "date", "index": "date"})


def select_symbol_columns(data: DataFrame, symbol: str) -> DataFrame:
    """Select one symbol from multi-level columns, leaving flat frames unchanged."""
    if not isinstance(data.columns, pd.MultiIndex):
        return data

    for level in range(data.columns.nlevels):
        if symbol in data.columns.get_level_values(level):
            return data.xs(symbol, axis=1, level=level)

    return data.droplevel(0, axis=1)


def normalize_column_names(data: DataFrame) -> DataFrame:
    """Return a copy with lowercase, underscore-separated column names."""
    normalized = data.copy()
    normalized.columns = [
        str(column).lower().replace(" ", "_") for column in normalized.columns
    ]

    return normalized


def find_timestamp_column(data: DataFrame) -> str:
    """Return the first recognized timestamp column or raise ``ValueError``."""
    for column in TIMESTAMP_COLUMNS:
        if column in data.columns:
            return column

    raise ValueError(
        "CSV data must contain one timestamp column: "
        f"{', '.join(TIMESTAMP_COLUMNS)}."
    )


def parse_date_range(start: str, end: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Parse and validate an inclusive-start, exclusive-end date range."""
    start_timestamp = pd.Timestamp(start)
    end_timestamp = pd.Timestamp(end)

    if start_timestamp >= end_timestamp:
        raise ValueError("Start date must be before end date.")

    return start_timestamp, end_timestamp


def prepare_market_data(
    data: DataFrame,
    timestamp_column: str,
    start_timestamp: pd.Timestamp,
    end_timestamp: pd.Timestamp,
) -> DataFrame:
    """Validate OHLCV data and restrict it to the requested half-open range.

    Input rows must already be ordered and unique. This function deliberately
    rejects invalid data instead of sorting, filling, or otherwise repairing it.
    """
    prepared = data.copy()
    prepared[timestamp_column] = pd.to_datetime(
        prepared[timestamp_column],
        errors="raise",
    )
    missing_columns = [
        column for column in REQUIRED_OHLCV_COLUMNS if column not in prepared.columns
    ]
    if missing_columns:
        raise ValueError(
            "Market data is missing required columns: "
            f"{', '.join(missing_columns)}."
        )

    timestamps = prepared[timestamp_column]
    if timestamps.duplicated().any():
        raise ValueError("Market data must not contain duplicate timestamps.")

    if not timestamps.is_monotonic_increasing:
        raise ValueError("Market data must be sorted by timestamp in ascending order.")

    for column in REQUIRED_OHLCV_COLUMNS:
        prepared[column] = pd.to_numeric(prepared[column], errors="raise")

    if prepared.loc[:, REQUIRED_OHLCV_COLUMNS].isna().any().any():
        raise ValueError("OHLCV values must not be missing.")

    finite_values = prepared.loc[:, REQUIRED_OHLCV_COLUMNS].map(isfinite)
    if not finite_values.all().all():
        raise ValueError("OHLCV values must be finite.")

    price_columns = ("open", "high", "low", "close")
    if (prepared.loc[:, price_columns] <= 0).any().any():
        raise ValueError("OHLC prices must be positive.")

    if (prepared["volume"] < 0).any():
        raise ValueError("Volume must not be negative.")

    if (prepared["high"] < prepared["low"]).any():
        raise ValueError("OHLC high must be greater than or equal to low.")

    if (
        (prepared["open"] < prepared["low"])
        | (prepared["open"] > prepared["high"])
        | (prepared["close"] < prepared["low"])
        | (prepared["close"] > prepared["high"])
    ).any():
        raise ValueError("OHLC open and close must be between low and high.")

    return prepared.loc[
        (prepared[timestamp_column] >= start_timestamp)
        & (prepared[timestamp_column] < end_timestamp)
    ].reset_index(drop=True)

def candles_from_dataframe(
    data: DataFrame,
    timestamp_column: str | None = None,
) -> list[Candle]:
    """Convert normalized market-data rows to immutable ``Candle`` objects."""

    if timestamp_column is None:
        timestamp_column = find_timestamp_column(data)

    if timestamp_column not in data.columns:
        raise ValueError(
            f"Market data does not contain timestamp column: {timestamp_column}."
        )

    return [
        Candle(
            timestamp=pd.Timestamp(timestamp).to_pydatetime(),
            open=float(open_price),
            high=float(high_price),
            low=float(low_price),
            close=float(close_price),
            volume=float(volume),
        )
        for (
            timestamp,
            open_price,
            high_price,
            low_price,
            close_price,
            volume,
        ) in data.loc[
            :, [timestamp_column, *REQUIRED_OHLCV_COLUMNS]
        ].itertuples(index=False, name=None)
    ]
