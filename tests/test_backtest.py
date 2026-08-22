from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timedelta
from unittest.mock import Mock, call

from backtester.data.models import Candle
from backtester.engine.backtest import BacktestEngine
from backtester.exceptions.trading_errors import InsufficientFundsError
from backtester.portfolio.position_sizing import PositionSizer, SizingContext
from backtester.portfolio.trade import Order, Side, Trade
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


def make_portfolio_mock(
    cash: float = 1_000,
    *,
    position_quantity: int = 0,
    value_at_close: float | None = None,
) -> Mock:
    portfolio = Mock()
    portfolio.cash = cash
    portfolio.position_quantity.return_value = position_quantity
    portfolio.value.return_value = cash if value_at_close is None else value_at_close
    return portfolio


def make_broker_mock(
    portfolio: Mock | None = None,
    *,
    errors: Sequence[Exception] = (),
    on_execute: Callable[[Order, Mapping[str, float], datetime], None] | None = None,
) -> Mock:
    broker = Mock()
    broker.portfolio = portfolio or make_portfolio_mock()
    broker.trades = []
    pending_errors = list(errors)

    def execute(order: Order, prices: Mapping[str, float], timestamp: datetime) -> None:
        if pending_errors:
            raise pending_errors.pop(0)

        if on_execute is not None:
            on_execute(order, prices, timestamp)

        broker.trades.append(
            Trade(
                symbol=order.symbol,
                side=order.side,
                quantity=order.quantity,
                fill_price=prices[order.symbol],
                timestamp=timestamp,
            )
        )

    broker.execute.side_effect = execute
    return broker


def make_sizer_mock(*quantities: int) -> Mock:
    sizer = Mock(spec=PositionSizer)
    configured_quantities = quantities or (10,)

    if len(configured_quantities) == 1:
        sizer.calculate_size.return_value = configured_quantities[0]
    else:
        sizer.calculate_size.side_effect = configured_quantities

    return sizer


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
    broker: Mock | None = None,
    sizer: Mock | None = None,
) -> tuple[BacktestEngine, ScriptedStrategy, Mock]:
    strategy = ScriptedStrategy(signals)
    broker = broker or make_broker_mock()
    sizer = sizer or make_sizer_mock()
    engine = BacktestEngine(
        strategy=strategy,
        broker=broker,
        sizer=sizer,
        data=candles,
        symbol="AAPL",
    )

    return engine, strategy, broker


def test_empty_data_produces_empty_result_without_calling_strategy() -> None:
    engine, strategy, broker = make_engine([Signal.BUY], candles=[])

    result = engine.run()

    assert result.records == []
    assert result.orders == []
    assert result.trades == []
    assert strategy.received_lengths == []
    broker.execute.assert_not_called()


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
    broker.execute.assert_not_called()


def test_buy_signal_creates_no_order_when_sizer_returns_zero() -> None:
    candles = make_candles([(100, 100), (90, 90)])
    broker = make_broker_mock(make_portfolio_mock(cash=99))
    sizer = make_sizer_mock(0)
    engine, _, broker = make_engine(
        [Signal.BUY, Signal.HOLD], candles, broker, sizer
    )

    result = engine.run()

    assert result.orders == []
    assert result.trades == []
    broker.execute.assert_not_called()


def test_buy_signal_is_executed_on_next_candle_open() -> None:
    candles = make_candles([(100, 100), (90, 95)])
    engine, _, broker = make_engine([Signal.BUY, Signal.HOLD], candles)

    result = engine.run()

    assert len(result.orders) == 1
    assert result.orders[0].success is True
    assert result.orders[0].order == Order(
        symbol="AAPL",
        side=Side.BUY,
        quantity=10,
        timestamp=candles[0].timestamp,
    )
    broker.execute.assert_called_once_with(
        result.orders[0].order,
        {"AAPL": 90},
        candles[1].timestamp,
    )
    assert result.trades == broker.trades


def test_pending_intent_sizes_order_from_portfolio_and_next_open() -> None:
    candles = make_candles([(50, 60), (70, 75)])
    broker = make_broker_mock(
        make_portfolio_mock(cash=1_000, position_quantity=4)
    )
    sizer = make_sizer_mock(3)
    engine, _, _ = make_engine([Signal.BUY, Signal.HOLD], candles, broker, sizer)

    engine.run()

    sizer.calculate_size.assert_called_once_with(
        SizingContext(
            cash=1_000,
            current_quantity=4,
            portfolio_value=1_280,
            price=70,
        ),
        Side.BUY,
    )


def test_buy_signal_on_last_candle_is_not_executed() -> None:
    candles = make_candles([(100, 100)])
    engine, _, broker = make_engine([Signal.BUY], candles)

    result = engine.run()

    assert result.orders == []
    assert result.trades == []
    broker.execute.assert_not_called()


def test_sell_signal_creates_no_order_when_sizer_returns_zero() -> None:
    candles = make_candles([(20, 20), (25, 25)])
    sizer = make_sizer_mock(0)
    engine, _, broker = make_engine(
        [Signal.SELL, Signal.HOLD], candles, sizer=sizer
    )

    result = engine.run()

    assert result.orders == []
    assert result.trades == []
    broker.execute.assert_not_called()


def test_sell_signal_is_executed_on_next_candle_open() -> None:
    candles = make_candles([(20, 20), (25, 30)])
    broker = make_broker_mock(make_portfolio_mock(cash=100, position_quantity=5))
    sizer = make_sizer_mock(5)
    engine, _, broker = make_engine(
        [Signal.SELL, Signal.HOLD], candles, broker, sizer
    )

    result = engine.run()

    assert len(result.orders) == 1
    assert result.orders[0].success is True
    assert result.orders[0].order == Order(
        symbol="AAPL",
        side=Side.SELL,
        quantity=5,
        timestamp=candles[0].timestamp,
    )
    broker.execute.assert_called_once_with(
        result.orders[0].order,
        {"AAPL": 25},
        candles[1].timestamp,
    )


def test_failed_pending_order_is_recorded_without_trade() -> None:
    candles = make_candles([(10, 10), (20, 20)])
    broker = make_broker_mock(
        make_portfolio_mock(cash=100),
        errors=[InsufficientFundsError()],
    )
    engine, _, broker = make_engine([Signal.BUY, Signal.HOLD], candles, broker)

    result = engine.run()

    assert len(result.orders) == 1
    assert result.orders[0].success is False
    assert isinstance(result.orders[0].reason, InsufficientFundsError)
    assert result.trades == []
    assert broker.execute.call_count == 1


def test_failed_pending_order_does_not_stop_current_candle_signal() -> None:
    candles = make_candles([(10, 10), (20, 50), (10, 10)])
    broker = make_broker_mock(
        make_portfolio_mock(cash=100),
        errors=[InsufficientFundsError()],
    )
    engine, _, broker = make_engine(
        [Signal.BUY, Signal.BUY, Signal.HOLD],
        candles,
        broker,
        make_sizer_mock(10, 2),
    )

    result = engine.run()

    assert [order.success for order in result.orders] == [False, True]
    assert isinstance(result.orders[0].reason, InsufficientFundsError)
    assert [call_args.args[0] for call_args in broker.execute.call_args_list] == [
        Order("AAPL", Side.BUY, quantity=10, timestamp=candles[0].timestamp),
        Order("AAPL", Side.BUY, quantity=2, timestamp=candles[1].timestamp),
    ]
    assert result.trades == [
        Trade("AAPL", Side.BUY, quantity=2, fill_price=10, timestamp=candles[2].timestamp)
    ]


def test_run_is_idempotent_and_does_not_execute_trades_twice() -> None:
    candles = make_candles([(100, 100), (90, 95)])
    engine, _, broker = make_engine([Signal.BUY, Signal.HOLD], candles)

    first_result = engine.run()
    second_result = engine.run()

    assert second_result is first_result
    assert len(second_result.trades) == 1
    assert broker.execute.call_count == 1


def test_record_after_pending_order_uses_current_portfolio_snapshot_at_close() -> None:
    candles = make_candles([(100, 100), (80, 120)])
    portfolio = make_portfolio_mock(cash=1_000, value_at_close=1_000)

    def mark_execution_visible_in_next_record(
        _order: Order,
        _prices: Mapping[str, float],
        _timestamp: datetime,
    ) -> None:
        portfolio.cash = 200
        portfolio.value.return_value = 1_400

    broker = make_broker_mock(
        portfolio,
        on_execute=mark_execution_visible_in_next_record,
    )
    engine, _, _ = make_engine([Signal.BUY, Signal.HOLD], candles, broker)

    result = engine.run()

    assert result.records[0].portfolio_value_at_close == 1_000
    assert result.records[0].cash == 1_000
    assert result.records[1].portfolio_value_at_close == 1_400
    assert result.records[1].cash == 200
    portfolio.value.assert_has_calls(
        [call(prices={"AAPL": 100}), call(prices={"AAPL": 120})]
    )


def test_pending_order_executes_before_current_candle_signal_is_generated() -> None:
    candles = make_candles([(100, 100), (90, 95), (110, 110)])
    portfolio = make_portfolio_mock(cash=1_000, position_quantity=0)

    def expose_position_after_buy(
        order: Order,
        _prices: Mapping[str, float],
        _timestamp: datetime,
    ) -> None:
        if order.side == Side.BUY:
            portfolio.position_quantity.return_value = order.quantity

    broker = make_broker_mock(portfolio, on_execute=expose_position_after_buy)
    engine, _, broker = make_engine(
        [Signal.BUY, Signal.SELL, Signal.HOLD],
        candles,
        broker,
    )

    result = engine.run()

    assert [call_args.args[0] for call_args in broker.execute.call_args_list] == [
        Order("AAPL", Side.BUY, quantity=10, timestamp=candles[0].timestamp),
        Order("AAPL", Side.SELL, quantity=10, timestamp=candles[1].timestamp),
    ]
    assert result.orders[1].success is True


def test_strategy_receives_only_candles_available_so_far() -> None:
    candles = make_candles([(10, 10), (11, 11), (12, 12)])
    engine, strategy, _ = make_engine(
        [Signal.HOLD, Signal.HOLD, Signal.HOLD],
        candles,
    )

    engine.run()

    assert strategy.received_lengths == [1, 2, 3]


def test_buy_hold_sell_sequence_emits_expected_pending_orders() -> None:
    candles = make_candles([(100, 100), (90, 100), (110, 110), (130, 130)])
    portfolio = make_portfolio_mock(cash=1_000, position_quantity=0)

    def expose_position_after_buy(
        order: Order,
        _prices: Mapping[str, float],
        _timestamp: datetime,
    ) -> None:
        if order.side == Side.BUY:
            portfolio.position_quantity.return_value = order.quantity

    broker = make_broker_mock(portfolio, on_execute=expose_position_after_buy)
    engine, _, broker = make_engine(
        [Signal.BUY, Signal.HOLD, Signal.SELL, Signal.HOLD],
        candles,
        broker,
    )

    result = engine.run()

    assert [call_args.args[0] for call_args in broker.execute.call_args_list] == [
        Order("AAPL", Side.BUY, quantity=10, timestamp=candles[0].timestamp),
        Order("AAPL", Side.SELL, quantity=10, timestamp=candles[2].timestamp),
    ]
    assert [call_args.args[1] for call_args in broker.execute.call_args_list] == [
        {"AAPL": 90},
        {"AAPL": 130},
    ]
    assert [order.success for order in result.orders] == [True, True]
