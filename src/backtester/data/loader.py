from abc import ABC

import yfinance as yf
from pandas import DataFrame


class DataSource(ABC):
    def load(self, symbol: str, start: str, end: str) -> DataFrame | None:
        pass

class YFinanceDataSource(DataSource):
    def load(self, symbol: str, start: str, end: str) -> DataFrame | None:
        return yf.download(symbol, start=start, end=end, period='1d')