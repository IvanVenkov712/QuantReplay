from datetime import date
from pathlib import Path

import pytest

from backtester import cli
from backtester.engine.broker import (
    FixedCommissionModel,
    NoCommissionModel,
    ProportionalCommissionModel,
)
from backtester.engine.execution import ExecutionModel
from backtester.portfolio.position_sizing import (
    AllInAllOutSizer,
    FixedSizer,
    PercentSizer,
)
from backtester.portfolio.trade import Side


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_parse_args_uses_backtest_defaults_when_no_command_is_given() -> None:
    args = cli._parse_args([])

    assert args.command == "backtest"
    assert args.config == cli.DEFAULT_CONFIG_PATH
    assert args.symbol == cli.DEFAULT_SYMBOL
    assert args.years == cli.DEFAULT_YEARS
    assert args.source == "yfinance"
    assert args.initial_capital == cli.DEFAULT_INITIAL_CAPITAL
    assert args.sizing == cli.DEFAULT_SIZING
    assert args.buy_size is None
    assert args.sell_size is None
    assert args.buy_percent is None
    assert args.sell_percent is None
    assert args.commission_model == cli.DEFAULT_COMMISSION_MODEL
    assert args.fixed_commission is None
    assert args.commission_rate is None
    assert args.slippage_rate == cli.DEFAULT_SLIPPAGE_RATE
    assert args.strategy == "moving-average"
    assert args.short_window == cli.DEFAULT_SHORT_WINDOW
    assert args.long_window == cli.DEFAULT_LONG_WINDOW


def test_parse_args_loads_explicit_toml_configuration(tmp_path: Path) -> None:
    config_path = _write_config(
        tmp_path,
        """
[backtest]
symbol = "AAPL"
years = 3
initial_capital = 25000.0
sizing = "fixed"
buy_size = 4
sell_size = 2
commission_model = "fixed"
fixed_commission = 1.5
strategy = "rsi"
rsi_period = 10
rsi_min = 25.0
rsi_max = 75.0
""",
    )

    args = cli._parse_args(["--config", str(config_path)])

    assert args.config == config_path
    assert args.symbol == "AAPL"
    assert args.years == 3
    assert args.initial_capital == 25_000
    assert args.sizing == "fixed"
    assert args.buy_size == 4
    assert args.sell_size == 2
    assert args.commission_model == "fixed"
    assert args.fixed_commission == 1.5
    assert args.strategy == "rsi"
    assert args.rsi_period == 10
    assert args.rsi_min == 25
    assert args.rsi_max == 75
    assert args.short_window == cli.DEFAULT_SHORT_WINDOW


def test_cli_options_override_toml_and_toml_overrides_defaults(
    tmp_path: Path,
) -> None:
    config_path = _write_config(
        tmp_path,
        """
[backtest]
symbol = "AAPL"
years = 3
initial_capital = 25000.0
""",
    )

    args = cli._parse_args(
        [
            "--config",
            str(config_path),
            "--symbol",
            "MSFT",
            "--years",
            "2",
        ]
    )

    assert args.symbol == "MSFT"  # CLI beats TOML.
    assert args.years == 2  # CLI beats TOML.
    assert args.initial_capital == 25_000  # TOML beats the code default.
    assert args.strategy == "moving-average"  # No CLI/TOML value: code default.


def test_cli_selector_override_discards_dependent_values_for_old_toml_choice(
    tmp_path: Path,
) -> None:
    config_path = _write_config(
        tmp_path,
        """
[backtest]
sizing = "percent"
buy_percent = 0.5
sell_percent = 1.0
commission_model = "proportional"
commission_rate = 0.001
""",
    )

    args = cli._parse_args(
        [
            "--config",
            str(config_path),
            "--sizing",
            "fixed",
            "--buy-size",
            "4",
            "--sell-size",
            "2",
            "--commission-model",
            "fixed",
            "--fixed-commission",
            "1.5",
        ]
    )

    assert args.sizing == "fixed"
    assert args.buy_size == 4
    assert args.sell_size == 2
    assert args.buy_percent is None
    assert args.sell_percent is None
    assert args.commission_model == "fixed"
    assert args.fixed_commission == 1.5
    assert args.commission_rate is None


def test_parse_args_loads_default_config_from_current_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_config(tmp_path, "[backtest]\nsymbol = 'AAPL'\n", "quantreplay.toml")
    monkeypatch.chdir(tmp_path)

    args = cli._parse_args([])

    assert args.config == cli.DEFAULT_CONFIG_PATH
    assert args.symbol == "AAPL"


def test_compare_uses_backtest_and_compare_config_sections(tmp_path: Path) -> None:
    config_path = _write_config(
        tmp_path,
        """
[backtest]
symbol = "MSFT"
strategy = "mean-reversion"

[compare]
benchmark = "rsi"
""",
    )

    args = cli._parse_args(["compare", "--config", str(config_path)])

    assert args.command == "compare"
    assert args.symbol == "MSFT"
    assert args.strategy == "mean-reversion"
    assert args.benchmark == "rsi"


def test_config_option_may_precede_explicit_compare_command(tmp_path: Path) -> None:
    config_path = _write_config(
        tmp_path,
        "[backtest]\nsymbol = 'MSFT'\n[compare]\nbenchmark = 'rsi'\n",
    )

    args = cli._parse_args(["--config", str(config_path), "compare"])

    assert args.command == "compare"
    assert args.symbol == "MSFT"
    assert args.benchmark == "rsi"


def test_parse_args_rejects_missing_explicit_config_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    missing_path = tmp_path / "missing.toml"

    with pytest.raises(SystemExit) as exc_info:
        cli._parse_args(["--config", str(missing_path)])

    assert exc_info.value.code == 2
    assert "Configuration file does not exist" in capsys.readouterr().err


def test_toml_values_use_the_same_argparse_validation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config_path = _write_config(tmp_path, "[backtest]\nyears = 0\n")

    with pytest.raises(SystemExit) as exc_info:
        cli._parse_args(["--config", str(config_path)])

    assert exc_info.value.code == 2
    assert "value must be a positive integer" in capsys.readouterr().err


def test_parse_args_accepts_backtest_options_without_explicit_command() -> None:
    csv_path = Path("prices.csv")

    args = cli._parse_args(
        [
            "--source",
            "csv",
            "--csv-path",
            str(csv_path),
            "--symbol",
            "AAPL",
            "--strategy",
            "rsi",
            "--rsi-period",
            "10",
            "--rsi-min",
            "25",
            "--rsi-max",
            "75",
            "--initial-capital",
            "25000",
        ]
    )

    assert args.command == "backtest"
    assert args.source == "csv"
    assert args.csv_path == csv_path
    assert args.symbol == "AAPL"
    assert args.strategy == "rsi"
    assert args.rsi_period == 10
    assert args.rsi_min == 25
    assert args.rsi_max == 75
    assert args.initial_capital == 25_000


def test_parse_args_accepts_compare_command_and_benchmark() -> None:
    args = cli._parse_args(
        [
            "compare",
            "--strategy",
            "mean-reversion",
            "--benchmark",
            "rsi",
        ]
    )

    assert args.command == "compare"
    assert args.strategy == "mean-reversion"
    assert args.benchmark == "rsi"


@pytest.mark.parametrize(
    ("arguments", "expected_type"),
    [
        ([], AllInAllOutSizer),
        (
            ["--sizing", "fixed", "--buy-size", "3", "--sell-size", "2"],
            FixedSizer,
        ),
        (
            [
                "--sizing",
                "percent",
                "--buy-percent",
                "0.4",
                "--sell-percent",
                "0.25",
            ],
            PercentSizer,
        ),
    ],
)
def test_create_sizer_uses_selected_policy(
    arguments: list[str],
    expected_type: type,
) -> None:
    args = cli._parse_args(arguments)

    assert isinstance(cli._create_sizer(args), expected_type)


@pytest.mark.parametrize(
    ("arguments", "expected_type"),
    [
        ([], NoCommissionModel),
        (
            ["--commission-model", "fixed", "--fixed-commission", "2.50"],
            FixedCommissionModel,
        ),
        (
            [
                "--commission-model",
                "proportional",
                "--commission-rate",
                "0.001",
            ],
            ProportionalCommissionModel,
        ),
    ],
)
def test_create_commission_model_uses_selected_policy(
    arguments: list[str],
    expected_type: type,
) -> None:
    args = cli._parse_args(arguments)

    assert isinstance(cli._create_commission_model(args), expected_type)


def test_create_execution_model_uses_selected_slippage_rate() -> None:
    args = cli._parse_args(["--slippage-rate", "0.01"])

    model = cli._create_execution_model(args)

    assert isinstance(model, ExecutionModel)
    assert model.calculate_fill_price(100, Side.BUY) == pytest.approx(101)


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        (
            ["--sizing", "fixed", "--buy-size", "3"],
            "--buy-size and --sell-size are required when --sizing fixed is used",
        ),
        (
            ["--sizing", "percent", "--buy-percent", "0.5"],
            "--buy-percent and --sell-percent are required when --sizing percent is used",
        ),
        (
            ["--buy-size", "3"],
            "--buy-size and --sell-size may only be used with --sizing fixed",
        ),
        (
            ["--buy-percent", "0.5"],
            "--buy-percent and --sell-percent may only be used with --sizing percent",
        ),
    ],
)
def test_parse_args_rejects_incomplete_or_irrelevant_sizing_options(
    arguments: list[str],
    message: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli._parse_args(arguments)

    assert exc_info.value.code == 2
    assert message in capsys.readouterr().err


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        (
            ["--commission-model", "fixed"],
            "--fixed-commission is required when --commission-model fixed is used",
        ),
        (
            ["--fixed-commission", "2.50"],
            "--fixed-commission may only be used with --commission-model fixed",
        ),
        (
            ["--commission-model", "proportional"],
            "--commission-rate is required when --commission-model proportional is used",
        ),
        (
            ["--commission-rate", "0.001"],
            "--commission-rate may only be used with --commission-model proportional",
        ),
    ],
)
def test_parse_args_rejects_incomplete_or_irrelevant_commission_options(
    arguments: list[str],
    message: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli._parse_args(arguments)

    assert exc_info.value.code == 2
    assert message in capsys.readouterr().err


@pytest.mark.parametrize("value", ["-0.01", "1.01", "nan", "inf"])
def test_parse_args_rejects_percentage_outside_zero_to_one(
    value: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli._parse_args(
            [
                "--sizing",
                "percent",
                "--buy-percent",
                value,
                "--sell-percent",
                "0.5",
            ]
        )

    assert exc_info.value.code == 2
    assert "value must be between 0 and 1" in capsys.readouterr().err


@pytest.mark.parametrize("value", ["-0.01", "1", "nan", "inf"])
def test_parse_args_rejects_invalid_slippage_rate(
    value: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli._parse_args(["--slippage-rate", value])

    assert exc_info.value.code == 2
    assert "value must be between 0 (inclusive) and 1 (exclusive)" in (
        capsys.readouterr().err
    )


@pytest.mark.parametrize("value", ["-0.01", "nan", "inf"])
def test_parse_args_rejects_invalid_fixed_commission(
    value: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli._parse_args(
            ["--commission-model", "fixed", "--fixed-commission", value]
        )

    assert exc_info.value.code == 2
    assert "value must be a non-negative finite number" in capsys.readouterr().err


@pytest.mark.parametrize("command", ["backtest", "compare"])
def test_csv_source_requires_csv_path(
    command: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli._parse_args([command, "--source", "csv"])

    assert exc_info.value.code == 2
    assert "--csv-path is required when --source csv is used" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("option", "value", "message"),
    [
        ("--years", "0", "value must be a positive integer"),
        ("--short-window", "-1", "value must be a positive integer"),
        ("--initial-capital", "0", "value must be positive"),
    ],
)
def test_parse_args_rejects_non_positive_values(
    option: str,
    value: str,
    message: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli._parse_args([option, value])

    assert exc_info.value.code == 2
    assert message in capsys.readouterr().err


def test_resolve_date_range_handles_leap_day_when_subtracting_years() -> None:
    assert cli._resolve_date_range(None, "2024-02-29", 1) == (
        "2023-02-28",
        "2024-02-29",
    )


def test_resolve_date_range_rejects_start_on_or_after_end() -> None:
    with pytest.raises(ValueError, match="Start date must be before end date"):
        cli._resolve_date_range("2024-01-02", "2024-01-02", 5)


def test_resolve_date_range_uses_today_when_end_is_omitted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FixedDate(date):
        @classmethod
        def today(cls) -> "FixedDate":
            return cls(2026, 8, 19)

    monkeypatch.setattr(cli, "date", FixedDate)

    assert cli._resolve_date_range(None, None, 2) == (
        "2024-08-19",
        "2026-08-19",
    )


def test_main_runs_backtest_from_csv_and_prints_parameters_and_metrics(
    capsys: pytest.CaptureFixture[str],
) -> None:
    csv_path = FIXTURES_DIR / "cli_two_candles.csv"

    exit_code = cli.main(
        [
            "backtest",
            "--source",
            "csv",
            "--csv-path",
            str(csv_path),
            "--symbol",
            "AAPL",
            "--start",
            "2024-01-01",
            "--end",
            "2024-01-03",
            "--strategy",
            "buy-and-hold",
            "--initial-capital",
            "10000",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert "Backtest parameters" in captured.out
    assert "Strategy: BuyAndHoldStrategy" in captured.out
    assert "Asset: AAPL" in captured.out
    assert "Period: 2024-01-01 to 2024-01-03" in captured.out
    assert f"Data source: CSVDataSource({csv_path})" in captured.out
    assert "Initial capital: 10,000.00" in captured.out
    assert "Position sizing: AllInAllOutSizer" in captured.out
    assert "Commission: NoCommissionModel" in captured.out
    assert "Slippage: ExecutionModel(rate=0.00%)" in captured.out
    assert "Performance metrics" in captured.out
    assert "Total return: 10.00%" in captured.out
    assert "Number of trades: 1" in captured.out


@pytest.mark.parametrize("timestamp_column", ["timestamp", "datetime"])
def test_main_accepts_supported_csv_timestamp_aliases(
    timestamp_column: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    csv_path = tmp_path / "prices.csv"
    csv_path.write_text(
        (
            f"{timestamp_column},open,high,low,close,volume\n"
            "2024-01-01,100,100,100,100,1000\n"
            "2024-01-02,100,110,100,110,1200\n"
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "backtest",
            "--source",
            "csv",
            "--csv-path",
            str(csv_path),
            "--symbol",
            "AAPL",
            "--start",
            "2024-01-01",
            "--end",
            "2024-01-03",
            "--strategy",
            "buy-and-hold",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert "Total return: 10.00%" in captured.out
    assert "Number of trades: 1" in captured.out


def test_main_runs_backtest_using_toml_configuration(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    csv_path = (FIXTURES_DIR / "cli_two_candles.csv").as_posix()
    config_path = _write_config(
        tmp_path,
        f"""
[backtest]
source = "csv"
csv_path = "{csv_path}"
symbol = "AAPL"
start = "2024-01-01"
end = "2024-01-03"
strategy = "buy-and-hold"
initial_capital = 10000.0
""",
    )

    exit_code = cli.main(["--config", str(config_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert "Strategy: BuyAndHoldStrategy" in captured.out
    assert "Asset: AAPL" in captured.out
    assert "Total return: 10.00%" in captured.out


def test_main_runs_backtest_with_fixed_position_sizing(
    capsys: pytest.CaptureFixture[str],
) -> None:
    csv_path = FIXTURES_DIR / "cli_two_candles.csv"

    exit_code = cli.main(
        [
            "backtest",
            "--source",
            "csv",
            "--csv-path",
            str(csv_path),
            "--start",
            "2024-01-01",
            "--end",
            "2024-01-03",
            "--strategy",
            "buy-and-hold",
            "--sizing",
            "fixed",
            "--buy-size",
            "1",
            "--sell-size",
            "1",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert "Position sizing: FixedSizer(buy=1, sell=1)" in captured.out
    assert "Total return: 0.10%" in captured.out
    assert "Number of trades: 1" in captured.out


def test_main_applies_and_prints_fixed_commission_and_slippage(
    capsys: pytest.CaptureFixture[str],
) -> None:
    csv_path = FIXTURES_DIR / "cli_two_candles.csv"

    exit_code = cli.main(
        [
            "backtest",
            "--source",
            "csv",
            "--csv-path",
            str(csv_path),
            "--start",
            "2024-01-01",
            "--end",
            "2024-01-03",
            "--strategy",
            "buy-and-hold",
            "--sizing",
            "fixed",
            "--buy-size",
            "1",
            "--sell-size",
            "1",
            "--commission-model",
            "fixed",
            "--fixed-commission",
            "5",
            "--slippage-rate",
            "0.1",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert "Commission: FixedCommissionModel(per_trade=5.00)" in captured.out
    assert "Slippage: ExecutionModel(rate=10.00%)" in captured.out
    assert "Total return: -0.05%" in captured.out
    assert "Number of trades: 1" in captured.out


def test_main_compares_strategy_with_benchmark_using_same_csv_data(
    capsys: pytest.CaptureFixture[str],
) -> None:
    csv_path = FIXTURES_DIR / "cli_two_candles.csv"

    exit_code = cli.main(
        [
            "compare",
            "--source",
            "csv",
            "--csv-path",
            str(csv_path),
            "--symbol",
            "AAPL",
            "--start",
            "2024-01-01",
            "--end",
            "2024-01-03",
            "--strategy",
            "buy-and-hold",
            "--benchmark",
            "moving-average",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert "Benchmark comparison parameters" in captured.out
    assert "Strategy: BuyAndHoldStrategy" in captured.out
    assert "Benchmark: MovingAverageCrossStrategy(20, 50)" in captured.out
    assert "Metric differences" in captured.out
    assert "Total return difference: 10.00%" in captured.out
    assert "Number of trades difference: 1" in captured.out


def test_main_reports_runtime_errors_and_returns_nonzero_exit_code(
    capsys: pytest.CaptureFixture[str],
) -> None:
    csv_path = FIXTURES_DIR / "cli_one_candle.csv"

    exit_code = cli.main(
        [
            "--source",
            "csv",
            "--csv-path",
            str(csv_path),
            "--start",
            "2024-01-01",
            "--end",
            "2024-01-02",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert (
        captured.err
        == "Error: At least two candles are required to calculate metrics.\n"
    )


@pytest.mark.parametrize(
    ("name", "value", "expected"),
    [
        ("total_return", 0.12345, "12.35%"),
        ("daily_sharpe_ratio", 1.23456, "1.2346"),
        ("number_of_trades", 3.0, "3"),
        ("daily_sharpe_ratio", float("nan"), "N/A"),
        ("daily_sharpe_ratio", float("inf"), "N/A"),
    ],
)
def test_format_metric_value_uses_metric_specific_formatting(
    name: str,
    value: float,
    expected: str,
) -> None:
    assert cli._format_metric_value(name, value) == expected


def _write_config(
    tmp_path: Path,
    contents: str,
    filename: str = "settings.toml",
) -> Path:
    path = tmp_path / filename
    path.write_text(contents.strip() + "\n", encoding="utf-8")
    return path
