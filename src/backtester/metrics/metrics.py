from abc import ABC, abstractmethod
from collections.abc import Callable
from math import sqrt
from typing import List

from typing_extensions import override, NamedTuple

from engine.backtest_result import BacktestResult

class Metric(ABC):
    def __init__(self, name: str, label: str):

        self._name: str = name
        self._label: str = label

    @property
    def name(self) -> str:
        return self._name

    @property
    def label(self) -> str:
        return self._label

    @abstractmethod
    def calculate(self, results: BacktestResult) -> float:
        pass

class FunctionMetric(Metric):
    def __init__(self, name: str, label: str, function: Callable[[BacktestResult], float]):
        super().__init__(name, label)
        self._function: Callable[[BacktestResult], float] = function

    @override
    def calculate(self, results: BacktestResult) -> float:
        return self._function(results)

class MetricData(NamedTuple):
    label: str
    result: float

class PerformanceAnalyzer:
    def __init__(self):
        self._metrics: dict[str, Metric] = {}

    def add_metric(self, metric: Metric):
        if metric.name in self._metrics:
            raise ValueError("metric name must be unique")
        self._metrics[metric.name] = metric

    def add_metric_func(
            self, name: str, label: str,
            function: Callable[[BacktestResult], float]):

        self.add_metric(FunctionMetric(name, label, function))

    def calculate_metrics(self, results: BacktestResult) -> dict[str, MetricData]:
        return {
            name: MetricData(metric.label, metric.calculate(results))
            for name, metric in self._metrics.items()
        }

def total_return(results: BacktestResult) -> float:
    vn = results.records[-1].portfolio_value_at_close
    v1 = results.records[0].portfolio_value_at_close
    return vn / v1 - 1

def annualized_return(results: BacktestResult) -> float:
    t = (results.records[-1].timestamp - results.records[0].timestamp).days / 365.25
    vn = results.records[-1].portfolio_value_at_close
    v1 = results.records[0].portfolio_value_at_close
    return (vn / v1) ** (1 / t) - 1

def period_returns(results: BacktestResult) -> List[float]:
    returns = []
    for prev, next in zip(results.records, results.records[1:]):
        v_prev = prev.portfolio_value_at_close
        v_curr = next.portfolio_value_at_close
        t = v_curr / v_prev - 1
        returns.append(t)

    return returns

def daily_avg(results: BacktestResult) -> float:
    rets = period_returns(results)
    n = len(rets)
    if n <= 0:
        return 0
    return sum(rets) / n

def daily_volatility(results: BacktestResult) -> float:
    rets = period_returns(results)
    n = len(rets)
    if n <= 1:
        return 0
    avg = sum(rets) / n
    variance = sum((r - avg) ** 2 for r in rets) / (n - 1)
    return sqrt(variance)

def annual_volatility(results: BacktestResult) -> float:
    return daily_volatility(results) * sqrt(252)

def max_drawdown(results: BacktestResult) -> float:
    curr_max = float("-inf")
    drawdowns = []
    for r in results.records:
        v = r.portfolio_value_at_close
        if v > curr_max:
            curr_max = v

        drawdowns.append(v / curr_max - 1)

    return min(drawdowns)

def daily_sharpe_ratio(results: BacktestResult) -> float:
    return daily_avg(results) / daily_volatility(results)

def annual_sharpe_ratio(results: BacktestResult) -> float:
    return daily_sharpe_ratio(results) * sqrt(252)

def number_of_trades(results: BacktestResult) -> float:
    return len(results.trades)

