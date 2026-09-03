from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from backtester.data.loader import CSVDataSource, YFinanceDataSource, prepare_market_data


def write_csv(path: Path, content: str) -> None:
    path.write_text(content.strip(), encoding="utf-8")


def make_market_data(**overrides: object) -> pd.DataFrame:
    values = {
        "date": [pd.Timestamp("2024-01-01")],
        "open": [100],
        "high": [110],
        "low": [90],
        "close": [105],
        "volume": [1_000],
    }
    values.update(overrides)

    return pd.DataFrame(values)


def prepare_single_row_market_data(data: pd.DataFrame) -> pd.DataFrame:
    return prepare_market_data(
        data,
        timestamp_column="date",
        start_timestamp=pd.Timestamp("2024-01-01"),
        end_timestamp=pd.Timestamp("2024-01-02"),
    )


def test_yfinance_data_source_normalizes_downloaded_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    downloaded_data = pd.DataFrame(
        {
            "Open": [99, 103],
            "High": [104, 107],
            "Low": [98, 102],
            "Close": [103, 106],
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

    monkeypatch.setattr("backtester.data.loader.yf.download", fake_download)

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
            "auto_adjust": True,
            "progress": False,
            "multi_level_index": False,
        }
    ]
    assert data.loc[:, ["date", "open", "high", "low", "close", "volume"]].to_dict(
        orient="list"
    ) == {
        "date": [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-02")],
        "open": [99, 103],
        "high": [104, 107],
        "low": [98, 102],
        "close": [103, 106],
        "volume": [1000, 1200],
    }


def test_yfinance_adjustment_removes_ex_dividend_price_discontinuity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dates = pd.DatetimeIndex(
        [pd.Timestamp("2024-03-14"), pd.Timestamp("2024-03-15")],
        name="Date",
    )

    def fake_download(**kwargs: object) -> pd.DataFrame:
        if kwargs["auto_adjust"] is not True:
            return pd.DataFrame(
                {
                    "Open": [100, 99],
                    "High": [101, 100],
                    "Low": [99, 98],
                    "Close": [100, 99],
                    "Adj Close": [99, 99],
                    "Volume": [1_000, 1_000],
                },
                index=dates,
            )

        # The $1 raw-price drop is a dividend distribution, not an ordinary
        # investment loss. yfinance exposes the adjusted series as OHLC.
        return pd.DataFrame(
            {
                "Open": [99, 99],
                "High": [99.99, 100],
                "Low": [98.01, 98],
                "Close": [99, 99],
                "Volume": [1_000, 1_000],
            },
            index=dates,
        )

    monkeypatch.setattr("backtester.data.loader.yf.download", fake_download)

    data = YFinanceDataSource().load(
        symbol="DIVIDEND_STOCK",
        start="2024-03-14",
        end="2024-03-16",
    )

    assert data is not None
    assert data["close"].tolist() == [99, 99]
    assert data["close"].pct_change().iloc[1] == pytest.approx(0)


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


def test_csv_data_source_finds_first_available_date_for_selected_symbol(
    tmp_path: Path,
) -> None:
    csv_path = tmp_path / "prices.csv"
    write_csv(
        csv_path,
        """
        date,symbol,open,high,low,close,volume
        2023-01-03,MSFT,200,205,198,204,800
        2024-01-02,AAPL,100,105,99,104,1000
        2024-01-03,AAPL,104,108,103,107,1200
        """,
    )

    first_date = CSVDataSource(csv_path).first_available_date("AAPL")

    assert first_date == date(2024, 1, 2)


def test_csv_data_source_rejects_first_date_lookup_for_missing_symbol(
    tmp_path: Path,
) -> None:
    csv_path = tmp_path / "prices.csv"
    write_csv(
        csv_path,
        """
        date,symbol,open,high,low,close,volume
        2024-01-02,AAPL,100,105,99,104,1000
        """,
    )

    with pytest.raises(ValueError, match="no rows for symbol: MSFT"):
        CSVDataSource(csv_path).first_available_date("MSFT")


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


def test_prepare_market_data_rejects_missing_ohlcv_values() -> None:
    data = make_market_data(close=[None])

    with pytest.raises(ValueError, match="OHLCV values must not be missing"):
        prepare_single_row_market_data(data)


def test_prepare_market_data_rejects_non_finite_ohlcv_values() -> None:
    data = make_market_data(close=[float("inf")])

    with pytest.raises(ValueError, match="OHLCV values must be finite"):
        prepare_single_row_market_data(data)


def test_prepare_market_data_rejects_high_below_low() -> None:
    data = make_market_data(high=[89], low=[90])

    with pytest.raises(ValueError, match="high must be greater than or equal to low"):
        prepare_single_row_market_data(data)


def test_prepare_market_data_rejects_open_outside_high_low_range() -> None:
    data = make_market_data(open=[111])

    with pytest.raises(ValueError, match="open and close must be between low and high"):
        prepare_single_row_market_data(data)


def test_prepare_market_data_rejects_close_outside_high_low_range() -> None:
    data = make_market_data(close=[89])

    with pytest.raises(ValueError, match="open and close must be between low and high"):
        prepare_single_row_market_data(data)
