import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import PercentFormatter

from backtester.domain.trading import Signal, Side
from backtester.engine.backtest_result import BacktestResult
from backtester.visualization.charts import plot_close_prices, plot_signal_markers, plot_trade_markers, plot_equity, \
    plot_cash, plot_market_value, plot_position_quantity, plot_drawdown


def populate_price_panel(axes: Axes, result: BacktestResult) -> None:
    plot_close_prices(axes, result)
    plot_signal_markers(axes, result, Signal.BUY)
    plot_signal_markers(axes, result, Signal.SELL)
    plot_trade_markers(axes, result, Side.BUY)
    plot_trade_markers(axes, result, Side.SELL)
    axes.set_title(label="Price")

def populate_portfolio_panel(axes: Axes, result: BacktestResult) -> None:
    plot_equity(axes, result)
    plot_cash(axes, result)
    plot_market_value(axes, result)
    axes.set_title(label="Portfolio")

def populate_position_panel(axes: Axes, result: BacktestResult) -> None:
    plot_position_quantity(axes, result)
    axes.set_title(label="Position")

def populate_risk_panel(axes: Axes, result: BacktestResult) -> None:
    plot_drawdown(axes, result)
    axes.yaxis.set_major_formatter(PercentFormatter(xmax=1.0))
    axes.set_title(label="Risk (Drawdown)")


def create_backtest_figure(result: BacktestResult) -> Figure:
    figure, (price_ax, portfolio_ax, position_ax, risk_ax) = plt.subplots(4, 1, figsize=(10, 20))
    populate_risk_panel(price_ax, result)
    populate_portfolio_panel(portfolio_ax, result)
    populate_position_panel(position_ax, result)
    populate_risk_panel(risk_ax, result)

    return figure