from __future__ import annotations

import argparse
import math
import sys
from datetime import date
from pathlib import Path
from typing import Sequence, TextIO

from backtester.config import (
    DEFAULT_CONFIG_PATH,
    ConfigError,
    config_to_cli_arguments,
    load_config,
)
from backtester.data.loader import (
    CSVDataSource,
    DataSource,
    YFinanceDataSource,
    candles_from_dataframe,
)
from backtester.engine.backtest import BacktestEngine
from backtester.engine.backtest_result import BacktestResult
from backtester.engine.broker import (
    Broker,
    CommissionModel,
    FixedCommissionModel,
    NoCommissionModel,
    ProportionalCommissionModel,
)
from backtester.engine.execution import ExecutionModel
from backtester.metrics.benchmark_comparison import get_differences
from backtester.metrics.metrics import (
    MetricData,
    PerformanceAnalyzer,
    annual_sharpe_ratio,
    annual_volatility,
    annualized_return,
    daily_avg,
    daily_sharpe_ratio,
    daily_volatility,
    max_drawdown,
    number_of_trades,
    total_return,
)
from backtester.portfolio.portfolio import Portfolio
from backtester.portfolio.position_sizing import (
    AllInAllOutSizer,
    FixedSizer,
    PercentSizer,
    PositionSizer,
)
from backtester.strategies.base import Strategy
from backtester.strategies.buy_n_hold import BuyAndHoldStrategy
from backtester.strategies.moving_average import MovingAverageCrossStrategy
from backtester.strategies.mrma import MeanReversionStrategy
from backtester.strategies.rsi_simple import SimpleRSIStrategy


DEFAULT_SYMBOL = "SPY"
DEFAULT_YEARS = 5
DEFAULT_INITIAL_CAPITAL = 10_000.0
DEFAULT_SHORT_WINDOW = 20
DEFAULT_LONG_WINDOW = 50
DEFAULT_BENCHMARK = "buy-and-hold"
DEFAULT_SIZING = "all-in-all-out"
DEFAULT_COMMISSION_MODEL = "none"
DEFAULT_SLIPPAGE_RATE = 0.0

PERCENT_METRICS = {
    "total_return",
    "annualized_return",
    "daily_avg",
    "daily_volatility",
    "annual_volatility",
    "max_drawdown",
}


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)

    try:
        if args.command == "compare":
            _run_compare_command(args, sys.stdout)
        else:
            _run_backtest_command(args, sys.stdout)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    raw_args = _normalize_command_args(list(sys.argv[1:] if argv is None else argv))

    parser = _build_parser()
    try:
        config_path, is_explicit = _find_config_path(raw_args)
        config = load_config(config_path, required=is_explicit)
    except ConfigError as exc:
        parser.error(str(exc))

    command = raw_args[0]
    config_args = config_to_cli_arguments(
        config,
        command,
        cli_overrides=_find_cli_selector_overrides(raw_args[1:]),
    )
    args = parser.parse_args([command, *config_args, *raw_args[1:]])

    if args.source == "csv" and args.csv_path is None:
        parser.error("--csv-path is required when --source csv is used.")

    _validate_sizing_args(parser, args)
    _validate_commission_args(parser, args)

    return args


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="quantreplay",
        description="Run QuantReplay strategy backtests from the console.",
    )
    subparsers = parser.add_subparsers(dest="command")

    backtest_parser = subparsers.add_parser(
        "backtest",
        help="Run one strategy backtest and print its performance metrics.",
    )
    _add_common_arguments(backtest_parser)
    _add_strategy_arguments(backtest_parser)
    backtest_parser.set_defaults(command="backtest")

    compare_parser = subparsers.add_parser(
        "compare",
        help="Compare one strategy against a benchmark strategy.",
    )
    _add_common_arguments(compare_parser)
    _add_strategy_arguments(compare_parser)
    compare_parser.add_argument(
        "--benchmark",
        choices=["buy-and-hold", "moving-average", "rsi", "mean-reversion"],
        default=DEFAULT_BENCHMARK,
        help="Benchmark strategy used for comparison. Default: buy-and-hold.",
    )
    compare_parser.set_defaults(command="compare")

    return parser


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=(
            "TOML configuration path. If omitted, quantreplay.toml in the "
            "current working directory is used when present."
        ),
    )
    parser.add_argument(
        "--symbol",
        default=DEFAULT_SYMBOL,
        help=f"Asset symbol to test. Default: {DEFAULT_SYMBOL}.",
    )
    parser.add_argument(
        "--years",
        type=_positive_int,
        default=DEFAULT_YEARS,
        help=f"Number of calendar years to load when --start is omitted. Default: {DEFAULT_YEARS}.",
    )
    parser.add_argument(
        "--start",
        help="Inclusive start date in YYYY-MM-DD format. Defaults to --years before --end.",
    )
    parser.add_argument(
        "--end",
        help="Exclusive end date in YYYY-MM-DD format. Default: today's date.",
    )
    parser.add_argument(
        "--source",
        choices=["yfinance", "csv"],
        default="yfinance",
        help="Market data source. Default: yfinance.",
    )
    parser.add_argument(
        "--csv-path",
        type=Path,
        help="CSV file or directory used when --source csv is selected.",
    )
    parser.add_argument(
        "--initial-capital",
        type=_positive_float,
        default=DEFAULT_INITIAL_CAPITAL,
        help=f"Initial portfolio cash. Default: {DEFAULT_INITIAL_CAPITAL:.0f}.",
    )
    parser.add_argument(
        "--sizing",
        choices=["all-in-all-out", "fixed", "percent"],
        default=DEFAULT_SIZING,
        help=f"Position-sizing policy. Default: {DEFAULT_SIZING}.",
    )
    parser.add_argument(
        "--buy-size",
        type=_positive_int,
        help="Whole shares bought per buy signal when --sizing fixed is used.",
    )
    parser.add_argument(
        "--sell-size",
        type=_positive_int,
        help="Whole shares sold per sell signal when --sizing fixed is used.",
    )
    parser.add_argument(
        "--buy-percent",
        type=_percentage,
        help="Fraction of available cash used per buy signal with --sizing percent.",
    )
    parser.add_argument(
        "--sell-percent",
        type=_percentage,
        help="Fraction of owned shares sold per sell signal with --sizing percent.",
    )
    parser.add_argument(
        "--commission-model",
        choices=["none", "fixed", "proportional"],
        default=DEFAULT_COMMISSION_MODEL,
        help=(
            "Commission model applied to each trade. "
            f"Default: {DEFAULT_COMMISSION_MODEL}."
        ),
    )
    parser.add_argument(
        "--fixed-commission",
        type=_non_negative_float,
        help="Cash commission per trade required with --commission-model fixed.",
    )
    parser.add_argument(
        "--commission-rate",
        type=_percentage,
        help=(
            "Fraction of trade notional charged as commission with "
            "--commission-model proportional."
        ),
    )
    parser.add_argument(
        "--slippage-rate",
        type=_slippage_rate,
        default=DEFAULT_SLIPPAGE_RATE,
        help=(
            "Adverse fill-price adjustment as a fraction in [0, 1). "
            f"Default: {DEFAULT_SLIPPAGE_RATE:.0f}."
        ),
    )


def _add_strategy_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--strategy",
        choices=["moving-average", "buy-and-hold", "rsi", "mean-reversion"],
        default="moving-average",
        help="Strategy to test. Default: moving-average.",
    )
    parser.add_argument(
        "--short-window",
        type=_positive_int,
        default=DEFAULT_SHORT_WINDOW,
        help=f"Short moving average window. Default: {DEFAULT_SHORT_WINDOW}.",
    )
    parser.add_argument(
        "--long-window",
        type=_positive_int,
        default=DEFAULT_LONG_WINDOW,
        help=f"Long moving average window. Default: {DEFAULT_LONG_WINDOW}.",
    )
    parser.add_argument(
        "--rsi-period",
        type=_positive_int,
        default=14,
        help="RSI lookback period. Default: 14.",
    )
    parser.add_argument(
        "--rsi-min",
        type=float,
        default=30.0,
        help="RSI buy threshold. Default: 30.",
    )
    parser.add_argument(
        "--rsi-max",
        type=float,
        default=70.0,
        help="RSI sell threshold. Default: 70.",
    )
    parser.add_argument(
        "--mean-window",
        type=_positive_int,
        default=20,
        help="Mean reversion average window. Default: 20.",
    )
    parser.add_argument(
        "--mean-threshold",
        type=float,
        default=0.95,
        help="Mean reversion buy threshold as a fraction of the average. Default: 0.95.",
    )


def _run_backtest_command(args: argparse.Namespace, output: TextIO) -> None:
    start, end = _resolve_date_range(args.start, args.end, args.years)
    strategy = _create_strategy(args.strategy, args)
    result = _run_backtest(args, strategy, start, end)
    metrics = _create_performance_analyzer().calculate_metrics(result)

    _print_parameters(
        output=output,
        title="Backtest parameters",
        strategy_name=_describe_strategy(args.strategy, args),
        benchmark_name=None,
        symbol=args.symbol,
        start=start,
        end=end,
        years=args.years,
        data_source_name=_describe_data_source(args),
        initial_capital=args.initial_capital,
        sizing_name=_describe_sizing(args),
        commission_name=_describe_commission(args),
        slippage_name=_describe_slippage(args),
    )
    _print_metrics(output, "Performance metrics", metrics)


def _run_compare_command(args: argparse.Namespace, output: TextIO) -> None:
    start, end = _resolve_date_range(args.start, args.end, args.years)
    data_source = _create_data_source(args)
    data = data_source.load(args.symbol, start, end)
    if data is None or data.empty:
        raise ValueError("No market data was returned for the selected parameters.")

    candles = candles_from_dataframe(data)
    _validate_backtest_data(candles)

    strategy_result = _run_backtest_with_candles(
        strategy=_create_strategy(args.strategy, args),
        candles=candles,
        symbol=args.symbol,
        initial_capital=args.initial_capital,
        sizer=_create_sizer(args),
        execution_model=_create_execution_model(args),
        commission_model=_create_commission_model(args),
    )
    benchmark_result = _run_backtest_with_candles(
        strategy=_create_strategy(args.benchmark, args),
        candles=candles,
        symbol=args.symbol,
        initial_capital=args.initial_capital,
        sizer=_create_sizer(args),
        execution_model=_create_execution_model(args),
        commission_model=_create_commission_model(args),
    )

    analyzer = _create_performance_analyzer()
    strategy_metrics = analyzer.calculate_metrics(strategy_result)
    benchmark_metrics = analyzer.calculate_metrics(benchmark_result)
    differences = get_differences(strategy_metrics, benchmark_metrics)

    _print_parameters(
        output=output,
        title="Benchmark comparison parameters",
        strategy_name=_describe_strategy(args.strategy, args),
        benchmark_name=_describe_strategy(args.benchmark, args),
        symbol=args.symbol,
        start=start,
        end=end,
        years=args.years,
        data_source_name=_describe_data_source(args),
        initial_capital=args.initial_capital,
        sizing_name=_describe_sizing(args),
        commission_name=_describe_commission(args),
        slippage_name=_describe_slippage(args),
    )
    _print_metrics(output, "Metric differences", differences)


def _run_backtest(
    args: argparse.Namespace,
    strategy: Strategy,
    start: str,
    end: str,
) -> BacktestResult:
    data_source = _create_data_source(args)
    data = data_source.load(args.symbol, start, end)
    if data is None or data.empty:
        raise ValueError("No market data was returned for the selected parameters.")

    candles = candles_from_dataframe(data)
    _validate_backtest_data(candles)
    return _run_backtest_with_candles(
        strategy=strategy,
        candles=candles,
        symbol=args.symbol,
        initial_capital=args.initial_capital,
        sizer=_create_sizer(args),
        execution_model=_create_execution_model(args),
        commission_model=_create_commission_model(args),
    )


def _run_backtest_with_candles(
    strategy: Strategy,
    candles: Sequence,
    symbol: str,
    initial_capital: float,
    sizer: PositionSizer,
    execution_model: ExecutionModel,
    commission_model: CommissionModel,
) -> BacktestResult:
    broker = Broker(
        Portfolio(cash=initial_capital),
        execution_model=execution_model,
        commission_model=commission_model,
    )
    return BacktestEngine(
        strategy=strategy,
        broker=broker,
        sizer=sizer,
        data=candles,
        symbol=symbol,
    ).run()


def _create_performance_analyzer() -> PerformanceAnalyzer:
    analyzer = PerformanceAnalyzer()
    analyzer.add_metric_func("total_return", "Total return", total_return)
    analyzer.add_metric_func("annualized_return", "Annualized return", annualized_return)
    analyzer.add_metric_func("daily_avg", "Daily average return", daily_avg)
    analyzer.add_metric_func("daily_volatility", "Daily volatility", daily_volatility)
    analyzer.add_metric_func("annual_volatility", "Annual volatility", annual_volatility)
    analyzer.add_metric_func("max_drawdown", "Maximum drawdown", max_drawdown)
    analyzer.add_metric_func("daily_sharpe_ratio", "Daily Sharpe ratio", daily_sharpe_ratio)
    analyzer.add_metric_func(
        "annual_sharpe_ratio",
        "Annual Sharpe ratio",
        annual_sharpe_ratio,
    )
    analyzer.add_metric_func("number_of_trades", "Number of trades", number_of_trades)
    return analyzer


def _create_strategy(name: str, args: argparse.Namespace) -> Strategy:
    if name == "moving-average":
        return MovingAverageCrossStrategy(args.short_window, args.long_window)
    if name == "buy-and-hold":
        return BuyAndHoldStrategy()
    if name == "rsi":
        return SimpleRSIStrategy(args.rsi_period, args.rsi_min, args.rsi_max)
    if name == "mean-reversion":
        return MeanReversionStrategy(args.mean_window, args.mean_threshold)

    raise ValueError(f"Unknown strategy: {name}.")


def _create_sizer(args: argparse.Namespace) -> PositionSizer:
    if args.sizing == "all-in-all-out":
        return AllInAllOutSizer()
    if args.sizing == "fixed":
        return FixedSizer(buy_size=args.buy_size, sell_size=args.sell_size)
    if args.sizing == "percent":
        return PercentSizer(
            percent_buy=args.buy_percent,
            percent_sell=args.sell_percent,
        )

    raise ValueError(f"Unknown position sizing policy: {args.sizing}.")


def _create_execution_model(args: argparse.Namespace) -> ExecutionModel:
    return ExecutionModel(slippage_rate=args.slippage_rate)


def _create_commission_model(args: argparse.Namespace) -> CommissionModel:
    if args.commission_model == "none":
        return NoCommissionModel()
    if args.commission_model == "fixed":
        return FixedCommissionModel(commission=args.fixed_commission)
    if args.commission_model == "proportional":
        return ProportionalCommissionModel(percent=args.commission_rate)

    raise ValueError(f"Unknown commission model: {args.commission_model}.")


def _create_data_source(args: argparse.Namespace) -> DataSource:
    if args.source == "yfinance":
        return YFinanceDataSource()
    if args.source == "csv":
        return CSVDataSource(args.csv_path)

    raise ValueError(f"Unknown data source: {args.source}.")


def _resolve_date_range(
    start_arg: str | None,
    end_arg: str | None,
    years: int,
) -> tuple[str, str]:
    end = date.fromisoformat(end_arg) if end_arg else date.today()
    start = date.fromisoformat(start_arg) if start_arg else _subtract_years(end, years)

    if start >= end:
        raise ValueError("Start date must be before end date.")

    return start.isoformat(), end.isoformat()


def _subtract_years(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year - years)
    except ValueError:
        return value.replace(year=value.year - years, day=28)


def _validate_backtest_data(candles: Sequence) -> None:
    if len(candles) < 2:
        raise ValueError("At least two candles are required to calculate metrics.")


def _print_parameters(
    *,
    output: TextIO,
    title: str,
    strategy_name: str,
    benchmark_name: str | None,
    symbol: str,
    start: str,
    end: str,
    years: int,
    data_source_name: str,
    initial_capital: float,
    sizing_name: str,
    commission_name: str,
    slippage_name: str,
) -> None:
    print(title, file=output)
    print(f"Strategy: {strategy_name}", file=output)
    if benchmark_name is not None:
        print(f"Benchmark: {benchmark_name}", file=output)
    print(f"Asset: {symbol}", file=output)
    print(f"Period: {start} to {end}", file=output)
    print(f"Years parameter: {years}", file=output)
    print(f"Data source: {data_source_name}", file=output)
    print(f"Initial capital: {_format_money(initial_capital)}", file=output)
    print(f"Position sizing: {sizing_name}", file=output)
    print(f"Commission: {commission_name}", file=output)
    print(f"Slippage: {slippage_name}", file=output)
    print(file=output)


def _print_metrics(
    output: TextIO,
    title: str,
    metrics: dict[str, MetricData],
) -> None:
    print(title, file=output)
    for name, data in metrics.items():
        print(f"{data.label}: {_format_metric_value(name, data.result)}", file=output)


def _format_metric_value(name: str, value: float) -> str:
    if isinstance(value, float) and not math.isfinite(value):
        return "N/A"

    if name in PERCENT_METRICS:
        return f"{value:.2%}"

    if name == "number_of_trades":
        return str(int(value))

    return f"{value:.4f}"


def _format_money(value: float) -> str:
    return f"{value:,.2f}"


def _describe_strategy(name: str, args: argparse.Namespace) -> str:
    if name == "moving-average":
        return f"MovingAverageCrossStrategy({args.short_window}, {args.long_window})"
    if name == "buy-and-hold":
        return "BuyAndHoldStrategy"
    if name == "rsi":
        return f"SimpleRSIStrategy(period={args.rsi_period}, min={args.rsi_min}, max={args.rsi_max})"
    if name == "mean-reversion":
        return f"MeanReversionStrategy(window={args.mean_window}, threshold={args.mean_threshold})"

    raise ValueError(f"Unknown strategy: {name}.")


def _describe_data_source(args: argparse.Namespace) -> str:
    if args.source == "yfinance":
        return "YFinanceDataSource"

    return f"CSVDataSource({args.csv_path})"


def _describe_sizing(args: argparse.Namespace) -> str:
    if args.sizing == "all-in-all-out":
        return "AllInAllOutSizer"
    if args.sizing == "fixed":
        return f"FixedSizer(buy={args.buy_size}, sell={args.sell_size})"
    if args.sizing == "percent":
        return (
            "PercentSizer("
            f"buy={args.buy_percent:.2%}, sell={args.sell_percent:.2%}"
            ")"
        )

    raise ValueError(f"Unknown position sizing policy: {args.sizing}.")


def _describe_commission(args: argparse.Namespace) -> str:
    if args.commission_model == "none":
        return "NoCommissionModel"
    if args.commission_model == "fixed":
        return (
            "FixedCommissionModel("
            f"per_trade={_format_money(args.fixed_commission)}"
            ")"
        )
    if args.commission_model == "proportional":
        return f"ProportionalCommissionModel(rate={args.commission_rate:.2%})"

    raise ValueError(f"Unknown commission model: {args.commission_model}.")


def _describe_slippage(args: argparse.Namespace) -> str:
    return f"ExecutionModel(rate={args.slippage_rate:.2%})"


def _validate_sizing_args(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> None:
    fixed_values = (args.buy_size, args.sell_size)
    percent_values = (args.buy_percent, args.sell_percent)

    if args.sizing == "fixed" and any(value is None for value in fixed_values):
        parser.error(
            "--buy-size and --sell-size are required when --sizing fixed is used."
        )
    if args.sizing != "fixed" and any(value is not None for value in fixed_values):
        parser.error("--buy-size and --sell-size may only be used with --sizing fixed.")

    if args.sizing == "percent" and any(value is None for value in percent_values):
        parser.error(
            "--buy-percent and --sell-percent are required when --sizing percent is used."
        )
    if args.sizing != "percent" and any(
        value is not None for value in percent_values
    ):
        parser.error(
            "--buy-percent and --sell-percent may only be used with --sizing percent."
        )


def _validate_commission_args(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> None:
    if args.commission_model == "fixed" and args.fixed_commission is None:
        parser.error(
            "--fixed-commission is required when --commission-model fixed is used."
        )
    if args.commission_model != "fixed" and args.fixed_commission is not None:
        parser.error(
            "--fixed-commission may only be used with --commission-model fixed."
        )

    if args.commission_model == "proportional" and args.commission_rate is None:
        parser.error(
            "--commission-rate is required when "
            "--commission-model proportional is used."
        )
    if args.commission_model != "proportional" and args.commission_rate is not None:
        parser.error(
            "--commission-rate may only be used with --commission-model proportional."
        )


def _find_config_path(arguments: Sequence[str]) -> tuple[Path, bool]:
    """Return the final explicit --config value or the optional default path."""

    config_path: Path | None = None
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument == "--config":
            if index + 1 >= len(arguments) or arguments[index + 1].startswith("-"):
                raise ConfigError("--config requires a file path.")
            config_path = Path(arguments[index + 1])
            index += 2
            continue
        if argument.startswith("--config="):
            value = argument.partition("=")[2]
            if not value:
                raise ConfigError("--config requires a file path.")
            config_path = Path(value)

        index += 1

    if config_path is None:
        return DEFAULT_CONFIG_PATH, False

    return config_path, True


def _normalize_command_args(arguments: list[str]) -> list[str]:
    """Insert the default command and allow --config before an explicit command."""

    if not arguments:
        return ["backtest"]
    if arguments[0] in {"backtest", "compare"}:
        return arguments

    prefix_end = 0
    while prefix_end < len(arguments):
        argument = arguments[prefix_end]
        if argument == "--config" and prefix_end + 1 < len(arguments):
            prefix_end += 2
            continue
        if argument.startswith("--config="):
            prefix_end += 1
            continue
        break

    if prefix_end < len(arguments) and arguments[prefix_end] in {
        "backtest",
        "compare",
    }:
        command = arguments[prefix_end]
        return [command, *arguments[:prefix_end], *arguments[prefix_end + 1 :]]

    return ["backtest", *arguments]


def _find_cli_selector_overrides(arguments: Sequence[str]) -> dict[str, str]:
    """Find explicit CLI values that select models with dependent settings."""

    overrides: dict[str, str] = {}
    selectors = {"sizing", "commission_model"}
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument.startswith("--"):
            option, separator, inline_value = argument[2:].partition("=")
            name = option.replace("-", "_")
            if name in selectors:
                if separator:
                    overrides[name] = inline_value
                elif index + 1 < len(arguments):
                    overrides[name] = arguments[index + 1]
                    index += 1
        index += 1

    return overrides


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be a positive integer")

    return parsed


def _positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")

    return parsed


def _non_negative_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or parsed < 0:
        raise argparse.ArgumentTypeError("value must be a non-negative finite number")

    return parsed


def _percentage(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or not 0 <= parsed <= 1:
        raise argparse.ArgumentTypeError("value must be between 0 and 1")

    return parsed


def _slippage_rate(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or not 0 <= parsed < 1:
        raise argparse.ArgumentTypeError(
            "value must be between 0 (inclusive) and 1 (exclusive)"
        )

    return parsed


if __name__ == "__main__":
    raise SystemExit(main())
