"""Export completed backtest dashboards to image files."""

from pathlib import Path

from matplotlib import pyplot as plt

from backtester.engine.backtest_result import BacktestResult
from backtester.visualization.dashboard import create_backtest_figure


def export_backtest_dashboard(
    result: BacktestResult,
    output_path: str | Path,
    *,
    title: str | None = None,
    dpi: int = 150,
    overwrite: bool = False,
) -> Path:
    """Create and save a backtest dashboard, then close its figure.

    The output format is inferred by Matplotlib from the file extension.
    """
    path = Path(output_path)

    if not path.suffix:
        raise ValueError("Output path must include a file extension.")

    if dpi <= 0:
        raise ValueError("dpi must be positive.")

    if path.exists() and not overwrite:
        raise FileExistsError(f"Output file already exists: {path}")

    path.parent.mkdir(parents=True, exist_ok=True)

    figure = create_backtest_figure(result, title=title)
    try:
        figure.savefig(path, dpi=dpi, bbox_inches="tight")
    finally:
        plt.close(figure)

    return path
