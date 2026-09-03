"""Command-line application entry point."""

from __future__ import annotations

import sys
from typing import Sequence

from backtester.cli.arguments import parse_args
from backtester.cli.commands import run_backtest_command, run_compare_command


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Strat Echo command-line application."""
    args = parse_args(argv)

    try:
        if args.command == "compare":
            run_compare_command(args, sys.stdout)
        else:
            run_backtest_command(args, sys.stdout)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0
