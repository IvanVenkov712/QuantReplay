from matplotlib import pyplot as plt

from backtester.visualization.charts import plot_equity
from backtester.visualization.sample_data import load_results

figure, axes = plt.subplots(figsize=(10, 5))

plot_equity(axes, load_results())

figure.autofmt_xdate()
figure.tight_layout()
plt.show()