"""Individual Matplotlib charts for backtest results."""
from datetime import datetime
from typing import Callable

from matplotlib.axes import Axes

from backtester.domain.trading import Side, Signal
from backtester.engine.backtest_result import BacktestResult
from backtester.visualization.series import equity_series, cash_series, drawdown_series, trade_marker_series, \
    position_quantity_series, market_value_series, signal_marker_series, close_price_series


def plot_series(
        axes: Axes,
        result: BacktestResult,
        series_transformer: Callable[[BacktestResult], tuple[list[datetime], list[float | int]]],
        *,
        label: str,
        color: str
) -> None:
    timestamps, values = series_transformer(result)

    axes.plot(
        timestamps,
        values,
        label=label,
        color=color,
    )


def plot_markers(
        axes: Axes,
        result: BacktestResult,
        series_transformer: Callable[[BacktestResult], tuple[list[datetime], list[float | int]]],
        *,
        label: str,
        color: str,
        marker: str,
        filled: bool
) -> None:
    timestamps, values = series_transformer(result)

    axes.scatter(
        timestamps,
        values,
        marker=marker,
        label=label,
        s=60,
        zorder=3,
        color=color if filled else "none",
        edgecolors=color,
        linewidths=1.5,
    )


def plot_close_prices(axes: Axes, result: BacktestResult) -> None:
    transformer = lambda result: close_price_series(
        [record.candle for record in result.records]
    )

    plot_series(axes, result, transformer, label="Close prices", color="tab:cyan")

def plot_equity(axes: Axes, result: BacktestResult) -> None:
    """Plot total portfolio equity over time."""
    plot_series(axes, result, equity_series, label="Portfolio Equity", color="tab:blue")

def plot_cash(axes: Axes, result: BacktestResult) -> None:
   plot_series(axes, result, cash_series, label="Portfolio cash", color="tab:green")

def plot_drawdown(axes: Axes, result: BacktestResult) -> None:
   plot_series(axes, result, drawdown_series, label="Portfolio drawdown", color="tab:red")



def plot_trade_markers(axes: Axes, result: BacktestResult, side: Side) -> None:
    marker_by_side = {
        Side.BUY: "^",
        Side.SELL: "v"
    }
    color_by_side = {
        Side.BUY: "tab:green",
        Side.SELL: "tab:blue",
    }
    
    transformer = lambda result: trade_marker_series(result, side)
    label = f"Trade markers for side {side.value.title()}"

    plot_markers(
        axes, 
        result, 
        transformer, 
        label=label,
        color=color_by_side[side],
        marker=marker_by_side[side],
        filled=True,
    )
    
    

def plot_position_quantity(axes: Axes, result: BacktestResult) -> None:
    plot_series(axes, result, position_quantity_series, label="Position quantity", color="tab:brown")

def plot_market_value(axes: Axes, result: BacktestResult) -> None:
    plot_series(axes, result, market_value_series, label="Market value", color="tab:gray")

def plot_signal_markers(axes: Axes, result: BacktestResult, signal: Signal) -> None:
    marker_by_signal = {
        Signal.BUY: "^",
        Signal.SELL: "v",
        Signal.HOLD: "o",
    }
    
    color_by_signal = {
        Signal.BUY: "tab:green",
        Signal.SELL: "tab:blue",
        Signal.HOLD: "tab:gray"
    }
    title = f"Signal {signal.value.title()} Markers"

    transformer = lambda result: signal_marker_series(result, signal)
    plot_markers(
        axes, 
        result, 
        transformer, 
        label=title,
        color=color_by_signal[signal],
        marker=marker_by_signal[signal],
        filled=False,
    )
