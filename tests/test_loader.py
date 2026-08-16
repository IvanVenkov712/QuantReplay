from pathlib import Path

import pandas as pd
import pytest

from backtester.data.loader import CSVDataSource, YFinanceDataSource


def write_csv(path: Path, content: str) -> None:
    path.write_text(content.strip(), encoding="utf-8")


def test_yfinance_data_source_normalizes_downloaded_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    downloaded_data = pd.DataFrame(
        {
            "Open": [100, 104],
            "High": [105, 108],
            "Low": [99, 103],
            "Close": [104, 107],
            "Adj Close": [103, 106],
            "Volume": [1000, 1200],
        },
        index=pd.DatetimeIndex(
            [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-02")],
            name="Date",
        ),
    )
    download_calls: list[dict[str, object]] = []

    def fake_download(**kwargs: object) -> pd.DataFrame:
        download_calls.append(kwargs)
        return downloaded_data

    monkeypatch.setattr("src.backtester.data.loader.yf.download", fake_download)

    data = YFinanceDataSource().load(
        symbol="AAPL",
        start="2024-01-01",
        end="2024-01-03",
    )

    assert data is not None
    assert download_calls == [
        {
            "tickers": "AAPL",
            "start": "2024-01-01",
            "end": "2024-01-03",
            "interval": "1d",
            "auto_adjust": False,
            "progress": False,
            "multi_level_index": False,
        }
    ]
    assert data.loc[:, ["date", "open", "high", "low", "close", "volume"]].to_dict(
        orient="list"
    ) == {
        "date": [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-02")],
        "open": [100, 104],
        "high": [105, 108],
        "low": [99, 103],
        "close": [104, 107],
        "volume": [1000, 1200],
    }


def test_csv_data_source_loads_symbol_file_and_filters_dates(tmp_path: Path) -> None:
    write_csv(
        tmp_path / "AAPL.csv",
        """
        date,open,high,low,close,volume
        2024-01-01,100,105,99,104,1000
        2024-01-02,104,108,103,107,1200
        2024-01-03,107,109,106,108,900
        """,
    )

    data = CSVDataSource(tmp_path).load(
        symbol="AAPL",
        start="2024-01-02",
        end="2024-01-03",
    )

    assert data is not None
    assert data["date"].tolist() == [pd.Timestamp("2024-01-02")]
    assert data["close"].tolist() == [107]


def test_csv_data_source_filters_symbol_column_when_loading_single_file(
    tmp_path: Path,
) -> None:
    csv_path = tmp_path / "prices.csv"
    write_csv(
        csv_path,
        """
        date,symbol,open,high,low,close,volume
        2024-01-01,AAPL,100,105,99,104,1000
        2024-01-01,MSFT,200,205,198,204,800
        2024-01-02,AAPL,104,108,103,107,1200
        2024-01-02,MSFT,204,210,203,209,900
        """,
    )

    data = CSVDataSource(csv_path).load(
        symbol="MSFT",
        start="2024-01-01",
        end="2024-01-03",
    )

    assert data is not None
    assert data["symbol"].tolist() == ["MSFT", "MSFT"]
    assert data["close"].tolist() == [204, 209]


def test_csv_data_source_rejects_missing_ohlcv_columns(tmp_path: Path) -> None:
    csv_path = tmp_path / "AAPL.csv"
    write_csv(
        csv_path,
        """
        date,open,high,low,close
        2024-01-01,100,105,99,104
        """,
    )

    with pytest.raises(ValueError, match="missing required columns: volume"):
        CSVDataSource(csv_path).load("AAPL", "2024-01-01", "2024-01-02")


def test_csv_data_source_rejects_unsorted_timestamps(tmp_path: Path) -> None:
    csv_path = tmp_path / "AAPL.csv"
    write_csv(
        csv_path,
        """
        date,open,high,low,close,volume
        2024-01-02,104,108,103,107,1200
        2024-01-01,100,105,99,104,1000
        """,
    )

    with pytest.raises(ValueError, match="sorted by timestamp"):
        CSVDataSource(csv_path).load("AAPL", "2024-01-01", "2024-01-03")
