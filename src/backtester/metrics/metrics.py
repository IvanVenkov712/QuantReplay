"""Performance metric definitions for completed backtests."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from math import sqrt, isclose, nan
from typing import List

from typing_extensions import override, NamedTuple

from backtester.engine.backtest_result import BacktestResult

class Metric(ABC):
    """Named performance metric that can evaluate a backtest result."""

    def __init__(self, name: str, label: str):

        self._name: str = name
        self._label: str = label

    @property
    def name(self) -> str:
        """Return the unique key used to identify the metric."""
        return self._name

    @property
    def label(self) -> str:
        """Return the human-readable metric label."""
        return self._label

    @abstractmethod
    def calculate(self, results: BacktestResult) -> float:
        """Calculate the metric for a completed backtest."""
        pass

class FunctionMetric(Metric):
    """Adapt a metric-calculation function to the ``Metric`` interface."""

    def __init__(self, name: str, label: str, function: Callable[[BacktestResult], float]):
        super().__init__(name, label)
        self._function: Callable[[BacktestResult], float] = function

    @override
    def calculate(self, results: BacktestResult) -> float:
        """Evaluate the wrapped function for ``results``."""
        return self._function(results)

class MetricData(NamedTuple):
    """Human-readable label and calculated value for one metric."""

    label: str
    result: float

class PerformanceAnalyzer:
    """Register named metrics and calculate them as an ordered collection."""

    def __init__(self):
        self._metrics: dict[str, Metric] = {}

    def add_metric(self, metric: Metric):
        """Register a metric, rejecting duplicate metric names."""
        if metric.name in self._metrics:
            raise ValueError("metric name must be unique")
        self._metrics[metric.name] = metric

    def add_metric_func(
            self, name: str, label: str,
            function: Callable[[BacktestResult], float]):
        """Register a calculation function as a named metric."""

        self.add_metric(FunctionMetric(name, label, function))

    def calculate_metrics(self, results: BacktestResult) -> dict[str, MetricData]:
        """Calculate every registered metric for ``results``."""
        return {
            name: MetricData(metric.label, metric.calculate(results))
            for name, metric in self._metrics.items()
        }

def total_return(results: BacktestResult) -> float:
    """Return ``final_value / first_value - 1`` over recorded close values."""
    if not results.records:
        return 0
    vn = results.records[-1].portfolio_value_at_close
    v1 = results.records[0].portfolio_value_at_close
    if isclose(v1, 0):
        return float("+inf")
    return vn / v1 - 1

def annualized_return(results: BacktestResult) -> float:
    """Return CAGR using the elapsed calendar time and a 365.25-day year."""
    if not results.records:
        return 0
    elapsed_seconds = (results.records[-1].timestamp - results.records[0].timestamp).total_seconds()
    t =  elapsed_seconds / (3600.0 * 24 * 365.25)
    vn = results.records[-1].portfolio_value_at_close
    v1 = results.records[0].portfolio_value_at_close
    if isclose(v1, 0):
        return float("+inf")
    if isclose(t, 0):
        return 0
    return (vn / v1) ** (1 / t) - 1

def period_returns(results: BacktestResult) -> List[float]:
    """Return simple returns between consecutive recorded portfolio values."""
    returns = []
    for prev, next in zip(results.records, results.records[1:]):
        v_prev = prev.portfolio_value_at_close
        v_curr = next.portfolio_value_at_close
        if isclose(v_prev, 0):
            if isclose(v_curr, 0):
                t = 0
            else:
                t = float("+inf")
        else:
            t = v_curr / v_prev - 1
        returns.append(t)

    return returns

def daily_avg(results: BacktestResult) -> float:
    """Return the arithmetic mean of consecutive period returns."""
    rets = period_returns(results)
    n = len(rets)
    if n <= 0:
        return 0
    return sum(rets) / n

def daily_volatility(results: BacktestResult) -> float:
    """Return sample standard deviation of consecutive period returns."""
    rets = period_returns(results)
    n = len(rets)
    if n <= 1:
        return 0
    avg = sum(rets) / n
    variance = sum((r - avg) ** 2 for r in rets) / (n - 1)
    return sqrt(variance)

def annual_volatility(results: BacktestResult) -> float:
    """Annualize daily volatility using 252 trading periods per year."""
    return daily_volatility(results) * sqrt(252)

def max_drawdown(results: BacktestResult) -> float:
    """Return the worst fractional decline from a prior portfolio-value peak."""
    if not results.records:
        return 0.0
    curr_max = float("-inf")
    drawdowns = []
    for r in results.records:
        v = r.portfolio_value_at_close
        if v > curr_max:
            curr_max = v

        drawdowns.append(v / curr_max - 1)

    return min(drawdowns)

def daily_sharpe_ratio(results: BacktestResult) -> float:
    """Return mean daily return divided by volatility, assuming no risk-free return."""
    volatility = daily_volatility(results)
    if isclose(volatility, 0):
        return nan
    avg = daily_avg(results)
    return avg / volatility

def annual_sharpe_ratio(results: BacktestResult) -> float:
    """Annualize the zero-risk-free daily Sharpe ratio by ``sqrt(252)``."""
    return daily_sharpe_ratio(results) * sqrt(252)

def number_of_trades(results: BacktestResult) -> float:
    """Return the number of successfully executed trades."""
    return len(results.trades)

