from backtester.metrics.metrics import MetricData


def get_differences(
        strategy_metrics: dict[str, MetricData],
        benchmark_metrics: dict[str, MetricData]) -> dict[str, MetricData]:

    differences = {}
    for key, data in strategy_metrics.items():
        if key in benchmark_metrics:
            diff = data.result - benchmark_metrics[key].result
            differences[key] = MetricData(f"{data.label} difference", diff)

    return differences


