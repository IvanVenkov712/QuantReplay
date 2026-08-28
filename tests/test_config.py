from pathlib import Path

import pytest

from backtester.config import (
    ConfigError,
    config_to_cli_arguments,
    load_config,
)


PROJECT_ROOT = Path(__file__).parent.parent


def test_example_configuration_is_valid() -> None:
    config = load_config(PROJECT_ROOT / "quantreplay.example.toml", required=True)

    assert config["backtest"]["symbol"] == "SPY"
    assert config["backtest"]["strategy"] == "simple-moving-average"
    assert config["compare"]["benchmark"] == "buy-and-hold"


def test_load_config_returns_empty_document_when_optional_file_is_missing(
    tmp_path: Path,
) -> None:
    assert load_config(tmp_path / "missing.toml", required=False) == {}


def test_load_config_rejects_missing_explicit_file(tmp_path: Path) -> None:
    path = tmp_path / "missing.toml"

    with pytest.raises(ConfigError, match="Configuration file does not exist"):
        load_config(path, required=True)


def test_load_config_accepts_supported_sections_and_types(tmp_path: Path) -> None:
    path = _write_config(
        tmp_path,
        """
[backtest]
symbol = "AAPL"
years = 3
initial_capital = 25000.0
buffer_rate = 0.05
slippage_rate = 0.001

[compare]
benchmark = "rsi"
""",
    )

    assert load_config(path, required=True) == {
        "backtest": {
            "symbol": "AAPL",
            "years": 3,
            "initial_capital": 25_000.0,
            "buffer_rate": 0.05,
            "slippage_rate": 0.001,
        },
        "compare": {"benchmark": "rsi"},
    }


def test_config_to_cli_arguments_uses_compare_section_only_for_compare() -> None:
    config = {
        "backtest": {"symbol": "AAPL", "years": 3},
        "compare": {"benchmark": "rsi"},
    }

    assert config_to_cli_arguments(config, "backtest") == [
        "--symbol",
        "AAPL",
        "--years",
        "3",
    ]
    assert config_to_cli_arguments(config, "compare") == [
        "--symbol",
        "AAPL",
        "--years",
        "3",
        "--benchmark",
        "rsi",
    ]


@pytest.mark.parametrize(
    ("contents", "message"),
    [
        ("[unknown]\nvalue = 1\n", "Unknown configuration section"),
        ("[backtest]\nsymbl = 'SPY'\n", "Unknown option.*symbl"),
        ("[backtest]\nyears = 'five'\n", "years.*must be an integer"),
        ("backtest = 'not a table'\n", "must be a table"),
    ],
)
def test_load_config_rejects_unknown_names_and_wrong_types(
    tmp_path: Path,
    contents: str,
    message: str,
) -> None:
    path = _write_config(tmp_path, contents)

    with pytest.raises(ConfigError, match=message):
        load_config(path, required=True)


def test_load_config_wraps_toml_syntax_errors(tmp_path: Path) -> None:
    path = _write_config(tmp_path, "[backtest\nsymbol = 'SPY'\n")

    with pytest.raises(ConfigError, match="Invalid TOML"):
        load_config(path, required=True)


def _write_config(tmp_path: Path, contents: str) -> Path:
    path = tmp_path / "settings.toml"
    path.write_text(contents.strip() + "\n", encoding="utf-8")
    return path
