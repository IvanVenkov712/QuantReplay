from pathlib import Path
from unittest.mock import Mock, patch

import matplotlib
import pytest

matplotlib.use("Agg")

from matplotlib.figure import Figure

from backtester.engine.backtest_result import BacktestResult
from backtester.visualization import export


RESULT = BacktestResult(
    symbol="AAPL",
    initial_cash=1_000.0,
    records=[],
    trades=[],
    order_executions=[],
)


def test_export_backtest_dashboard_saves_and_closes_figure(tmp_path: Path) -> None:
    output_path = tmp_path / "reports" / "dashboard.png"
    figure = Mock(spec=Figure)

    with (
        patch.object(
            export,
            "create_backtest_figure",
            return_value=figure,
        ) as create_figure,
        patch.object(export.plt, "close") as close_figure,
    ):
        actual_path = export.export_backtest_dashboard(
            RESULT,
            str(output_path),
            title="BuyAndHoldStrategy — AAPL",
            dpi=200,
        )

    assert actual_path == output_path
    assert output_path.parent.is_dir()
    create_figure.assert_called_once_with(
        RESULT,
        title="BuyAndHoldStrategy — AAPL",
    )
    figure.savefig.assert_called_once_with(
        output_path,
        dpi=200,
        bbox_inches="tight",
    )
    close_figure.assert_called_once_with(figure)


def test_export_backtest_dashboard_rejects_path_without_extension(
    tmp_path: Path,
) -> None:
    with patch.object(export, "create_backtest_figure") as create_figure:
        with pytest.raises(
            ValueError,
            match="Output path must include a file extension",
        ):
            export.export_backtest_dashboard(RESULT, tmp_path / "dashboard")

    create_figure.assert_not_called()


@pytest.mark.parametrize("dpi", [0, -1])
def test_export_backtest_dashboard_rejects_non_positive_dpi(
    tmp_path: Path,
    dpi: int,
) -> None:
    with patch.object(export, "create_backtest_figure") as create_figure:
        with pytest.raises(ValueError, match="dpi must be positive"):
            export.export_backtest_dashboard(
                RESULT,
                tmp_path / "dashboard.png",
                dpi=dpi,
            )

    create_figure.assert_not_called()


def test_export_backtest_dashboard_does_not_overwrite_by_default(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "dashboard.png"
    output_path.write_bytes(b"existing image")

    with patch.object(export, "create_backtest_figure") as create_figure:
        with pytest.raises(FileExistsError, match="Output file already exists"):
            export.export_backtest_dashboard(RESULT, output_path)

    assert output_path.read_bytes() == b"existing image"
    create_figure.assert_not_called()


def test_export_backtest_dashboard_allows_explicit_overwrite(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "dashboard.png"
    output_path.write_bytes(b"existing image")
    figure = Mock(spec=Figure)

    with (
        patch.object(export, "create_backtest_figure", return_value=figure),
        patch.object(export.plt, "close") as close_figure,
    ):
        export.export_backtest_dashboard(RESULT, output_path, overwrite=True)

    figure.savefig.assert_called_once_with(
        output_path,
        dpi=150,
        bbox_inches="tight",
    )
    close_figure.assert_called_once_with(figure)


def test_export_backtest_dashboard_closes_figure_when_save_fails(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "dashboard.png"
    figure = Mock(spec=Figure)
    figure.savefig.side_effect = OSError("disk full")

    with (
        patch.object(export, "create_backtest_figure", return_value=figure),
        patch.object(export.plt, "close") as close_figure,
        pytest.raises(OSError, match="disk full"),
    ):
        export.export_backtest_dashboard(RESULT, output_path)

    close_figure.assert_called_once_with(figure)
