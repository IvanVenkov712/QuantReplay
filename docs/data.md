# Market data

QuantReplay obtains historical OHLCV candles from Yahoo Finance or CSV files.
Both sources are converted to the same internal `Candle` representation before
a backtest starts, so the engine does not depend directly on either source.

## Yahoo Finance

`YFinanceDataSource` downloads daily (`1d`) data through the `yfinance`
package. OHLC prices are requested without automatic adjustment
(`auto_adjust=False`). The requested start date is inclusive and the end date
is exclusive.

```powershell
python -m backtester.cli backtest --source yfinance --symbol SPY --start 2024-01-01 --end 2025-01-01
```

Downloaded column names are normalized before the data passes through the same
validation as CSV input.

## CSV files

Use `--source csv` together with `--csv-path`. The path may identify one file
or a directory. When given a directory, QuantReplay looks for
`<SYMBOL>.csv`; for example, the symbol `SPY` maps to `SPY.csv`.

A CSV file must contain one timestamp column named `date`, `timestamp`, or
`datetime`, plus all five OHLCV columns:

| Column | Required | Meaning |
| --- | --- | --- |
| `date`, `timestamp`, or `datetime` | One of these | Candle timestamp in a format understood by pandas |
| `open` | Yes | Opening price |
| `high` | Yes | Highest price |
| `low` | Yes | Lowest price |
| `close` | Yes | Closing price |
| `volume` | Yes | Traded volume |
| `symbol` | No | Allows one file to contain multiple symbols; matching rows are selected |

Column names are converted to lowercase and spaces are replaced with
underscores. If a `symbol` column is present, symbol matching is case-sensitive.

Example CSV:

```csv
date,symbol,open,high,low,close,volume
2024-01-02,SPY,472.16,473.67,470.49,472.65,12345678
2024-01-03,SPY,470.43,471.19,468.17,468.79,14567890
```

Example command:

```powershell
python -m backtester.cli backtest --source csv --csv-path data/SPY.csv --symbol SPY --start 2024-01-01 --end 2025-01-01
```

## Validation and normalization

Before data reaches the engine, QuantReplay requires:

- timestamps sorted in ascending order with no duplicates;
- numeric, finite, and non-missing OHLCV values;
- strictly positive `open`, `high`, `low`, and `close` prices;
- non-negative volume;
- `high` greater than or equal to `low`;
- `open` and `close` between `low` and `high`.

Rows outside the requested date range are removed. QuantReplay does not sort
rows, fill missing values, remove duplicate timestamps, resample candles, or
otherwise repair invalid market data automatically. Invalid input fails with a
clear error so that changes to financial data remain explicit.

See the [CLI reference](cli.md) for all source and date options, or return to
the [project README](../README.md).
