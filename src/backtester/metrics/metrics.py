from abc import ABC, abstractmethod
from collections import namedtuple
from collections.abc import Callable

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


class PerformanceAnalyzer:
    class MetricData(NamedTuple):
        label: str
        result: float

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

    def calculate_metrics(self, results: BacktestResult) -> dict[str, tuple[str, float]]:
        return {
            name: PerformanceAnalyzer.MetricData(metric.label, metric.calculate(results))
            for name, metric in self._metrics.items()
        }
