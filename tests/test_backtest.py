from collections.abc import Sequence
from datetime import datetime, timedelta

from backtester.data.models import Candle
from backtester.engine.backtest import BacktestEngine
from backtester.engine.broker import Broker
from backtester.exceptions.trading_errors import InsufficientFundsError
from backtester.portfolio.portfolio import Portfolio
from backtester.portfolio.trade import Side, Trade
from backtester.strategies.base import Signal, Strategy


class ScriptedStrategy(Strategy):
    def __init__(self, signals: Sequence[Signal]):
        self._signals = list(signals)
        self.received_lengths: list[int] = []

    def generate_signal(self, candles: Sequence[Candle]) -> Signal:
        self.received_lengths.append(len(candles))
        signal_index = len(candles) - 1

        if signal_index >= len(self._signals):
            return Signal.HOLD

        return self._signals[signal_index]


def make_candles(prices: Sequence[tuple[float, float]]) -> list[Candle]:
    start = datetime(2026, 1, 1)
    candles = []

    for index, (open_price, close_price) in enumerate(prices):
        candles.append(
            Candle(
                timestamp=start + timedelta(days=index),
                open=open_price,
                high=max(open_price, close_price),
                low=min(open_price, close_price),
                close=close_price,
                volume=1_000,
            )
        )

    return candles


def make_engine(
    signals: Sequence[Signal],
    candles: Sequence[Candle],
    portfolio: Portfolio | None = None,
) -> tuple[BacktestEngine, ScriptedStrategy, Broker]:
    strategy = ScriptedStrategy(signals)
    broker = Broker(portfolio or Portfolio(cash=1_000, positions={}))
    engine = BacktestEngine(strategy, broker, candles, symbol="AAPL")

    return engine, strategy, broker


def test_empty_data_produces_empty_result_without_calling_strategy() -> None:
    engine, strategy, broker = make_engine([Signal.BUY], candles=[])

    result = engine.run()

    assert result.records == []
    assert result.orders == []
    assert result.trades == []
    assert strategy.received_lengths == []
    assert broker.portfolio.cash == 1_000
    assert broker.portfolio.positions == {}


def test_hold_strategy_creates_records_without_orders_or_trades() -> None:
    candles = make_candles([(10, 10), (11, 11), (12, 12)])
    engine, _, broker = make_engine([Signal.HOLD, Signal.HOLD, Signal.HOLD], candles)

    result = engine.run()

    assert len(result.records) == 3
    assert [record.generated_signal for record in result.records] == [
        Signal.HOLD,
        Signal.HOLD,
        Signal.HOLD,
    ]
    assert result.orders == []
    assert result.trades == []
    assert broker.portfolio.cash == 1_000
    assert broker.portfolio.positions == {}


def test_buy_signal_creates_no_order_when_cash_cannot_buy_one_share() -> None:
    candles = make_candles([(100, 100), (90, 90)])
    portfolio = Portfolio(cash=99, positions={})
    engine, _, broker = make_engine([Signal.BUY, Signal.HOLD], candles, portfolio)

    result = engine.run()

    assert result.orders == []
    assert result.trades == []
    assert broker.portfolio.cash == 99
    assert broker.portfolio.positions == {}


def test_buy_signal_is_executed_on_next_candle_open() -> None:
    candles = make_candles([(100, 100), (90, 95)])
    engine, _, broker = make_engine([Signal.BUY, Signal.HOLD], candles)

    result = engine.run()

    expected_trade = Trade(
        symbol="AAPL",
        side=Side.BUY,
        quantity=10,
        price=90,
        timestamp=candles[1].timestamp,
    )
    assert result.trades == [expected_trade]
    assert result.orders[0].success is True
    assert result.orders[0].order.timestamp == candles[0].timestamp
    assert result.orders[0].order.quantity == 10
    assert broker.portfolio.cash == 100
    assert broker.portfolio.positions == {"AAPL": 10}


def test_buy_signal_on_last_candle_is_not_executed() -> None:
    candles = make_candles([(100, 100)])
    engine, _, broker = make_engine([Signal.BUY], candles)

    result = engine.run()

    assert result.orders == []
    assert result.trades == []
    assert broker.portfolio.cash == 1_000
    assert broker.portfolio.positions == {}


def test_sell_signal_creates_no_order_when_no_position_is_owned() -> None:
    candles = make_candles([(20, 20), (25, 25)])
    engine, _, broker = make_engine([Signal.SELL, Signal.HOLD], candles)

    result = engine.run()

    assert result.orders == []
    assert result.trades == []
    assert broker.portfolio.cash == 1_000
    assert broker.portfolio.positions == {}


def test_sell_signal_is_executed_on_next_candle_open() -> None:
    candles = make_candles([(20, 20), (25, 30)])
    portfolio = Portfolio(cash=100, positions={"AAPL": 5})
    engine, _, broker = make_engine([Signal.SELL, Signal.HOLD], candles, portfolio)

    result = engine.run()

    expected_trade = Trade(
        symbol="AAPL",
        side=Side.SELL,
        quantity=5,
        price=25,
        timestamp=candles[1].timestamp,
    )
    assert result.trades == [expected_trade]
    assert result.orders[0].success is True
    assert broker.portfolio.cash == 225
    assert broker.portfolio.positions == {}


def test_failed_pending_order_is_recorded_without_changing_portfolio() -> None:
    candles = make_candles([(10, 10), (20, 20)])
    portfolio = Portfolio(cash=100, positions={})
    engine, _, broker = make_engine([Signal.BUY, Signal.HOLD], candles, portfolio)

    result = engine.run()

    assert len(result.orders) == 1
    assert result.orders[0].success is False
    assert isinstance(result.orders[0].reason, InsufficientFundsError)
    assert result.trades == []
    assert broker.portfolio.cash == 100
    assert broker.portfolio.positions == {}


def test_failed_pending_order_does_not_stop_current_candle_signal() -> None:
    candles = make_candles([(10, 10), (20, 50), (10, 10)])
    portfolio = Portfolio(cash=100, positions={})
    engine, _, broker = make_engine([Signal.BUY, Signal.BUY, Signal.HOLD], candles, portfolio)

    result = engine.run()

    assert [order.success for order in result.orders] == [False, True]
    assert isinstance(result.orders[0].reason, InsufficientFundsError)
    assert result.trades == [
        Trade("AAPL", Side.BUY, quantity=2, price=10, timestamp=candles[2].timestamp)
    ]
    assert broker.portfolio.cash == 80
    assert broker.portfolio.positions == {"AAPL": 2}


def test_run_is_idempotent_and_does_not_execute_trades_twice() -> None:
    candles = make_candles([(100, 100), (90, 95)])
    engine, _, broker = make_engine([Signal.BUY, Signal.HOLD], candles)

    first_result = engine.run()
    second_result = engine.run()

    assert second_result is first_result
    assert len(second_result.trades) == 1
    assert broker.portfolio.cash == 100
    assert broker.portfolio.positions == {"AAPL": 10}


def test_record_after_pending_order_uses_updated_portfolio_at_close() -> None:
    candles = make_candles([(100, 100), (80, 120)])
    engine, _, _ = make_engine([Signal.BUY, Signal.HOLD], candles)

    result = engine.run()

    assert result.records[0].portfolio_value_at_close == 1_000
    assert result.records[0].cash == 1_000
    assert result.records[1].portfolio_value_at_close == 1_400
    assert result.records[1].cash == 200


def test_pending_order_executes_before_current_candle_signal_is_generated() -> None:
    candles = make_candles([(100, 100), (90, 95), (110, 110)])
    engine, _, broker = make_engine([Signal.BUY, Signal.SELL, Signal.HOLD], candles)

    result = engine.run()

    assert result.trades == [
        Trade("AAPL", Side.BUY, quantity=10, price=90, timestamp=candles[1].timestamp),
        Trade(
            "AAPL",
            Side.SELL,
            quantity=10,
            price=110,
            timestamp=candles[2].timestamp,
        ),
    ]
    assert [order.order.side for order in result.orders] == [Side.BUY, Side.SELL]
    assert broker.portfolio.cash == 1_200
    assert broker.portfolio.positions == {}


def test_strategy_receives_only_candles_available_so_far() -> None:
    candles = make_candles([(10, 10), (11, 11), (12, 12)])
    engine, strategy, _ = make_engine(
        [Signal.HOLD, Signal.HOLD, Signal.HOLD],
        candles,
    )

    engine.run()

    assert strategy.received_lengths == [1, 2, 3]


def test_buy_hold_sell_sequence_updates_cash_positions_and_trades() -> None:
    candles = make_candles([(100, 100), (90, 100), (110, 110), (130, 130)])
    engine, _, broker = make_engine(
        [Signal.BUY, Signal.HOLD, Signal.SELL, Signal.HOLD],
        candles,
    )

    result = engine.run()

    assert result.trades == [
        Trade("AAPL", Side.BUY, quantity=10, price=90, timestamp=candles[1].timestamp),
        Trade(
            "AAPL",
            Side.SELL,
            quantity=10,
            price=130,
            timestamp=candles[3].timestamp,
        ),
    ]
    assert [order.success for order in result.orders] == [True, True]
    assert broker.portfolio.cash == 1_400
    assert broker.portfolio.positions == {}
