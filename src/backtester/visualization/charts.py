"""Individual Matplotlib charts for backtest results."""
from datetime import datetime
from typing import Callable

from matplotlib.axes import Axes

from backtester.domain.trading import Side, Signal
from backtester.engine.backtest_result import BacktestResult
from backtester.visualization.series import equity_series, cash_series, drawdown_series, trade_marker_series, \
    position_quantity_series, market_value_series, signal_marker_series


def plot_series(
        axes: Axes,
        result: BacktestResult,
        series_transformer: Callable[[BacktestResult], tuple[list[datetime], list[float]]],
        *,
        title: str,
        color: str
):
    timestamps, values = series_transformer(result)

    axes.plot(
        timestamps,
        values,
        label=title,
        color=color,
    )
    axes.set_title(title)
    axes.set_ylabel("Value")
    axes.grid(alpha=0.3)
    axes.legend()


def plot_markers(
        axes: Axes,
        result: BacktestResult,
        series_transformer: Callable[[BacktestResult], tuple[list[datetime], list[float]]],
        *,
        title: str,
        color: str,
        marker: str
):
    timestamps, values = series_transformer(result)

    axes.scatter(
        timestamps,
        values,
        marker=marker,
        label=title,
        s=70,
        zorder=3,
        color=color
    )
    axes.set_title(title)
    axes.set_ylabel("Value")
    axes.grid(alpha=0.3)
    axes.legend()


def plot_equity(axes: Axes, result: BacktestResult) -> None:
    """Plot total portfolio equity over time."""
    plot_series(axes, result, equity_series, title="Portfolio Equity", color="tab:blue")

def plot_cash(axes: Axes, result: BacktestResult) -> None:
   plot_series(axes, result, cash_series, title="Portfolio cash", color="tab:green")

def plot_drawdown(axes: Axes, result: BacktestResult) -> None:
   plot_series(axes, result, drawdown_series, title="Portfolio drawdown", color="tab:red")

def plot_trade_marker(axes: Axes, result: BacktestResult, side: Side) -> None:
    marker_by_side = {
        Side.BUY: "^",
        Side.SELL: "v"
    }
    transformer = lambda result: trade_marker_series(result, side)
    title = f"Trade markers for side {side.value.title()}"
    plot_markers(axes, result, transformer, title=title, color="tab:purple", marker=marker_by_side[side])

def plot_position_quantity(axes: Axes, result: BacktestResult) -> None:
    plot_series(axes, result, position_quantity_series, title="Position quantity", color="tab:brown")

def plot_market_value(axes: Axes, result: BacktestResult) -> None:
    plot_series(axes, result, market_value_series, title="Market value", color="tab:gray")

def plot_signal_markers(axes: Axes, result: BacktestResult, signal: Signal) -> None:
    marker_by_signal = {
        Signal.BUY: "^",
        Signal.SELL: "v",
        Signal.HOLD: "o",
    }
    title = f"Signal {signal.value.title()} Markers"

    transformer = lambda result: signal_marker_series(result, signal)
    plot_markers(axes, result, transformer, title=title, color="tab:orange", marker=marker_by_signal[signal])
