from matplotlib import pyplot as plt

from backtester.domain.trading import Side, Signal
from backtester.visualization.charts import plot_equity, plot_cash, plot_drawdown, \
    plot_position_quantity, plot_market_value, plot_signal_markers, plot_trade_markers
from backtester.visualization.sample_data import load_results
results = load_results()

# figure, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 5))

figure, ax = plt.subplots(1, 1, figsize=(10, 5))


# plot_equity(ax1, results)
# plot_cash(ax2, results)
# plot_position_quantity(ax2, results)
# plot_drawdown(ax3, results)
# plot_trade_marker(ax4, results, Side.BUY)
print(__file__)
plot_trade_markers(ax, results, Side.BUY)
plot_trade_markers(ax, results, Side.SELL)

figure.autofmt_xdate()
figure.tight_layout()
plt.show()