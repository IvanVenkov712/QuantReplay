# AGENTS.md

## Project Overview

This repository contains a Python-based trading strategy backtesting system.

The project is primarily an educational and portfolio project. Its goals are:

1. Learn how a realistic backtesting engine works internally.
2. Practice clean Python architecture, testing, typing, and software design.
3. Learn basic quantitative finance concepts through implementation.
4. Produce a project substantial enough to demonstrate in a CV / GitHub portfolio.

This is NOT intended to become a production trading platform or a high-frequency trading system.

Prefer clarity, correctness, and educational value over unnecessary sophistication.

---

## Core Project Scope

The system should eventually support:

- loading historical OHLCV market data;
- representing candles / bars;
- defining trading strategies;
- generating buy / sell / hold signals;
- executing trades inside a backtest;
- maintaining cash and positions;
- calculating portfolio value over time;
- transaction fees and potentially slippage;
- calculating performance metrics;
- comparing strategies;
- visualizing backtest results.

Initial strategies may include:

- Buy and Hold;
- Moving Average Crossover;
- RSI-based strategy;
- possibly Bollinger Bands or another simple strategy later.

Do not add advanced quantitative techniques unless explicitly requested.

---

## Architecture

Prefer a modular architecture similar to:

src/
    data/
    models/
    strategies/
    engine/
    portfolio/
    metrics/
    visualization/

tests/

Exact module names may evolve as the project develops.

Important domain concepts should generally have explicit representations instead of being passed around as loosely structured dictionaries.

Examples:

- Candle
- Order
- Trade
- Position
- Portfolio
- Strategy
- BacktestResult

However, do not introduce classes merely for the sake of having more classes.

---

## Development Philosophy

This project is meant to be understood by its author.

When generating code:

- prefer simple and explicit implementations;
- avoid clever abstractions;
- avoid unnecessary design patterns;
- avoid premature optimization;
- avoid building frameworks inside the project;
- avoid large amounts of boilerplate;
- keep functions and classes reasonably small;
- make financial assumptions visible in the code.

A slightly longer implementation that is easy to understand is preferred over a compact but obscure implementation.

---

## AI Assistance Rules

Do not automatically implement large features end-to-end unless explicitly asked.

For non-trivial changes:

1. Explain the proposed approach briefly.
2. Identify the main classes/functions that will change.
3. Point out important financial or statistical assumptions.
4. Then implement the requested change.

When there are multiple reasonable architectures, explain the trade-offs instead of silently choosing the most sophisticated one.

The author wants to understand important project logic.

Be especially careful when modifying:

- backtesting execution logic;
- portfolio accounting;
- order execution;
- return calculations;
- financial metrics;
- strategy signal timing;
- anything that could introduce look-ahead bias.

Boilerplate, repetitive code, tests, typing, documentation, parsing, and similar mechanical work may be generated more aggressively.

---

## Backtesting Correctness

Correctness is more important than performance.

Pay special attention to:

### Look-ahead bias

A strategy must not use information that would not have been available at the simulated point in time.

For example, if a signal is computed using the closing price of day T, execution should normally happen no earlier than an explicitly defined execution point after that information becomes available.

Never silently use future rows of the dataset.

### Signal timing

Make signal timing explicit.

Clearly distinguish between:

- data used to produce a signal;
- time at which the signal becomes known;
- price used to execute the trade.

### Portfolio accounting

Portfolio value should clearly distinguish:

- cash;
- quantity of assets held;
- market value of positions;
- total equity.

### Transaction costs

If commissions or slippage are ignored, this should be explicit.

Do not hide assumptions.

### Missing data

Do not silently forward-fill or otherwise alter financial data unless explicitly intended.

---

## Financial Conventions

Unless specified otherwise:

- historical data consists primarily of OHLCV candles;
- one row represents one trading period;
- strategies operate chronologically;
- timestamps must remain ordered;
- prices should not be negative;
- volume should not be negative;
- portfolio state must never depend on future candles.

When implementing performance metrics, document the mathematical definition being used.

For example:

- total return;
- cumulative return;
- maximum drawdown;
- volatility;
- Sharpe ratio;
- win rate.

Do not assume that two formulas with the same common metric name are necessarily identical.

---

## Python Style

Use modern Python.

Preferred:

- Python 3.12+ compatible code;
- type hints for public APIs and important internal functions;
- `dataclasses` where they naturally fit;
- `pathlib.Path` instead of manual path manipulation;
- clear exceptions;
- small pure functions when possible.

Follow standard Python naming conventions.

Use:

- `snake_case` for functions and variables;
- `PascalCase` for classes;
- `UPPER_CASE` for constants.

Avoid wildcard imports.

Avoid mutable default arguments.

Prefer explicit dependencies over global state.

---

## Dependencies

Prefer the standard library where reasonable.

Likely acceptable dependencies include:

- pandas
- numpy
- matplotlib
- pytest

Additional libraries should only be introduced when they provide substantial value.

Do not add a large backtesting framework such as Backtrader, Zipline, or vectorbt to implement the core engine.

The point of this project is to implement and understand the important backtesting logic ourselves.

External libraries may still be used for:

- obtaining market data;
- numerical calculations;
- plotting;
- testing;
- supporting utilities.

---

## Testing

Important business logic should have automated tests.

Use pytest.

Tests should cover at least:

- candle/data validation;
- strategy signal generation;
- trade execution;
- cash updates;
- position updates;
- portfolio valuation;
- transaction fees if supported;
- performance metrics;
- edge cases.

Financial calculations should use small deterministic examples where the expected result can be calculated manually.

Prefer tests such as:

Initial cash: 1000
Buy: 10 shares at 20
Remaining cash: 800
Later price: 25
Portfolio equity: 1050

over tests whose expected values are difficult to independently verify.

Bug fixes should normally include a regression test.

---

## Data Handling

Keep data acquisition separate from backtesting logic.

The backtesting engine should ideally operate on already normalized historical data and should not depend directly on a specific external API.

Validate incoming data.

Expected fields will typically include:

- timestamp/date
- open
- high
- low
- close
- volume

The exact schema should be centralized rather than duplicated throughout the codebase.

---

## Strategy Design

Strategies should define trading logic, not manage portfolio accounting.

A strategy should generally answer a question such as:

> Given the historical information available up to this point, what action or signal should be produced?

The backtesting engine / portfolio components should decide how that signal affects holdings.

Avoid coupling strategies directly to CSV files, plotting libraries, or API clients.

---

## Performance

Do not optimize prematurely.

A straightforward loop over candles is acceptable for the initial version of the backtesting engine.

Readability and correct simulation semantics are more important than vectorization.

Vectorized implementations can be introduced later where appropriate and benchmarked against the reference implementation.

---

## Error Handling

Fail clearly when input is invalid.

Examples:

- missing required OHLCV columns;
- unsorted timestamps;
- duplicated timestamps where unsupported;
- invalid prices;
- insufficient data for an indicator;
- invalid initial capital;
- invalid commission configuration.

Do not silently recover from states that likely indicate a programming error.

---

## Documentation

Public classes and important functions should have concise docstrings.

Comments should explain WHY, not restate obvious Python syntax.

Financially non-obvious behavior should be documented.

The README should eventually explain:

- what the project does;
- architecture;
- installation;
- example usage;
- implemented strategies;
- assumptions;
- metrics;
- testing;
- limitations.

---

## Git / Change Scope

Keep changes focused.

Do not refactor unrelated code while implementing a small feature unless necessary.

Avoid changing public APIs without a reason.

When making a substantial architectural change, explain why it is preferable to the existing design.

---

## Things to Avoid

Do NOT:

- turn this into a live trading bot without explicit instruction;
- add broker integration without explicit instruction;
- introduce machine learning just because the project involves trading;
- add databases before persistence is actually needed;
- build a web frontend unless requested;
- overuse inheritance;
- create generic abstractions for hypothetical future requirements;
- optimize the engine before correctness is established;
- silently introduce look-ahead bias;
- assume profitable historical performance means a strategy is actually good.

---

## When Unsure

When a requested change involves a meaningful financial assumption, prefer making that assumption explicit.

For example:

> This implementation assumes that a signal calculated from today's close is executed at the next candle's open.

Do not silently choose behavior that can materially change backtest results.

When implementation complexity begins to grow substantially, prefer the simplest design that supports the current requirements.

## Learning Boundaries

The following parts are considered core learning material.

When working on them, prefer explanation + incremental implementation:

- backtest event loop;
- signal timing;
- order execution model;
- portfolio accounting;
- position management;
- drawdown calculation;
- return calculations;
- Sharpe ratio and related metrics;
- prevention of look-ahead bias.

The following parts may be automated more freely:

- project configuration;
- repetitive validation;
- test scaffolding;
- fixtures;
- serialization;
- CLI argument parsing;
- plotting boilerplate;
- documentation formatting;
- linting configuration;
- packaging configuration.