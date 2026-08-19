import pytest

from backtester.metrics.benchmark_comparison import get_differences
from backtester.metrics.metrics import MetricData


def test_get_differences_subtracts_benchmark_results_for_matching_metrics() -> None:
    strategy_metrics = {
        "total_return": MetricData("Total return", 0.25),
        "max_drawdown": MetricData("Max drawdown", -0.10),
        "strategy_only": MetricData("Strategy only", 1.0),
    }
    benchmark_metrics = {
        "total_return": MetricData("Total return", 0.20),
        "max_drawdown": MetricData("Max drawdown", -0.15),
        "benchmark_only": MetricData("Benchmark only", 2.0),
    }

    differences = get_differences(strategy_metrics, benchmark_metrics)

    assert set(differences) == {"total_return", "max_drawdown"}
    assert differences["total_return"].label == "Total return difference"
    assert differences["total_return"].result == pytest.approx(0.05)
    assert differences["max_drawdown"].label == "Max drawdown difference"
    assert differences["max_drawdown"].result == pytest.approx(0.05)


def test_get_differences_returns_empty_dict_when_no_metric_names_match() -> None:
    strategy_metrics = {"total_return": MetricData("Total return", 0.25)}
    benchmark_metrics = {"annual_return": MetricData("Annual return", 0.20)}

    assert get_differences(strategy_metrics, benchmark_metrics) == {}
