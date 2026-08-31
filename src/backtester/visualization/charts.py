"""Individual Matplotlib charts for backtest results."""

from matplotlib.axes import Axes

from backtester.engine.backtest_result import BacktestResult
from backtester.visualization.series import equity_series


def plot_equity(axes: Axes, result: BacktestResult) -> None:
    """Plot total portfolio equity over time."""
    timestamps, values = equity_series(result)

    axes.plot(
        timestamps,
        values,
        label="Portfolio equity",
        color="tab:blue",
    )
    axes.set_title("Portfolio equity")
    axes.set_ylabel("Value")
    axes.grid(alpha=0.3)
    axes.legend()