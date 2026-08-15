from abc import ABC
from pathlib import Path

import pandas as pd
import yfinance as yf
from pandas import DataFrame

REQUIRED_OHLCV_COLUMNS = ("open", "high", "low", "close", "volume")
TIMESTAMP_COLUMNS = ("timestamp", "date", "datetime")


class DataSource(ABC):
    def load(self, symbol: str, start: str, end: str) -> DataFrame | None:
        pass


class YFinanceDataSource(DataSource):
    def load(self, symbol: str, start: str, end: str) -> DataFrame | None:
        return yf.download(symbol, start=start, end=end, period='1d')


class CSVDataSource(DataSource):
    def __init__(self, path: Path):
        self.__path: Path = path

    def load(self, symbol: str, start: str, end: str) -> DataFrame | None:
        csv_path = self.__resolve_csv_path(symbol)

        data = pd.read_csv(csv_path)
        data.columns = [column.lower() for column in data.columns]

        if "symbol" in data.columns:
            data = data.loc[data["symbol"] == symbol].copy()

        timestamp_column = self.__find_timestamp_column(data)
        self.__validate_required_columns(data)

        data[timestamp_column] = pd.to_datetime(data[timestamp_column], errors="raise")
        self.__validate_chronological_order(data, timestamp_column)
        self.__validate_market_data(data)

        start_timestamp = pd.Timestamp(start)
        end_timestamp = pd.Timestamp(end)

        if start_timestamp >= end_timestamp:
            raise ValueError("Start date must be before end date.")

        return data.loc[
            (data[timestamp_column] >= start_timestamp)
            & (data[timestamp_column] < end_timestamp)
        ].reset_index(drop=True)

    def __resolve_csv_path(self, symbol: str) -> Path:
        if self.__path.is_dir():
            return self.__path / f"{symbol}.csv"

        return self.__path

    def __find_timestamp_column(self, data: DataFrame) -> str:
        for column in TIMESTAMP_COLUMNS:
            if column in data.columns:
                return column

        raise ValueError(
            "CSV data must contain one timestamp column: "
            f"{', '.join(TIMESTAMP_COLUMNS)}."
        )

    def __validate_required_columns(self, data: DataFrame) -> None:
        missing_columns = [
            column for column in REQUIRED_OHLCV_COLUMNS if column not in data.columns
        ]

        if missing_columns:
            raise ValueError(
                "CSV data is missing required columns: "
                f"{', '.join(missing_columns)}."
            )

    def __validate_chronological_order(
        self, data: DataFrame, timestamp_column: str
    ) -> None:
        timestamps = data[timestamp_column]

        if timestamps.duplicated().any():
            raise ValueError("CSV data must not contain duplicate timestamps.")

        if not timestamps.is_monotonic_increasing:
            raise ValueError("CSV data must be sorted by timestamp in ascending order.")

    def __validate_market_data(self, data: DataFrame) -> None:
        for column in REQUIRED_OHLCV_COLUMNS:
            data[column] = pd.to_numeric(data[column], errors="raise")

        price_columns = ("open", "high", "low", "close")
        if (data.loc[:, price_columns] <= 0).any().any():
            raise ValueError("OHLC prices must be positive.")

        if (data["volume"] < 0).any():
            raise ValueError("Volume must not be negative.")

