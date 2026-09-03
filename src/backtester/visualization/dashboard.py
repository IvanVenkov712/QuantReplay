"""Build a four-panel Matplotlib dashboard from a completed backtest."""

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import PercentFormatter

from backtester.domain.trading import Signal, Side
from backtester.engine.backtest_result import BacktestResult
from backtester.visualization.charts import plot_close_prices, plot_signal_markers, plot_trade_markers, plot_equity, \
    plot_cash, plot_market_value, plot_position_quantity, plot_drawdown


def populate_price_panel(axes: Axes, result: BacktestResult) -> None:
    """Plot closes, close-time signals, and fill-time trades with a legend."""
    plot_close_prices(axes, result)
    plot_signal_markers(axes, result, Signal.BUY)
    plot_signal_markers(axes, result, Signal.SELL)
    plot_trade_markers(axes, result, Side.BUY)
    plot_trade_markers(axes, result, Side.SELL)
    axes.set_title(label="Price")
    axes.legend()


def populate_portfolio_panel(axes: Axes, result: BacktestResult) -> None:
    """Plot total equity, cash, and invested market value with a legend."""
    plot_equity(axes, result)
    plot_cash(axes, result)
    plot_market_value(axes, result)
    axes.set_title(label="Portfolio")
    axes.legend()


def populate_position_panel(axes: Axes, result: BacktestResult) -> None:
    """Plot the result symbol's held quantity with a legend."""
    plot_position_quantity(axes, result)
    axes.set_title(label="Position")
    axes.legend()


def populate_risk_panel(axes: Axes, result: BacktestResult) -> None:
    """Plot fractional portfolio drawdown on a percentage-formatted axis."""
    plot_drawdown(axes, result)
    axes.yaxis.set_major_formatter(PercentFormatter(xmax=1.0))
    axes.set_title(label="Risk (Drawdown)")
    axes.legend()


def create_backtest_figure(
    result: BacktestResult,
    *,
    title: str | None = None,
) -> Figure:
    """Return a formatted price, portfolio, position, and risk dashboard.

    The panels share a time axis. The returned figure is not displayed, saved,
    or closed; those lifecycle operations remain the caller's responsibility.
    When supplied, ``title`` is displayed above the complete dashboard.
    """
    figure, (price_ax, portfolio_ax, position_ax, risk_ax) = plt.subplots(
        4,
        1,
        figsize=(10, 20),
        sharex=True,
    )
    populate_price_panel(price_ax, result)
    populate_portfolio_panel(portfolio_ax, result)
    populate_position_panel(position_ax, result)
    populate_risk_panel(risk_ax, result)
    if title is not None:
        figure.suptitle(title)
    figure.autofmt_xdate()
    if title is not None:
        figure.tight_layout(rect=(0.0, 0.0, 1.0, 0.98))
    else:
        figure.tight_layout()
    return figure
