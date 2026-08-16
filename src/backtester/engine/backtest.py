from typing import Sequence

from backtester.data.models import Candle
from backtester.engine.backtest_result import BacktestResult, OrderExecution, BacktestRecord
from backtester.engine.broker import Broker
from backtester.exceptions.trading_errors import InsufficientError
from backtester.portfolio.trade import Order, side_from_signal, Side
from backtester.strategies.base import Strategy, Signal


class BacktestEngine:
    def __init__(
            self, strategy: Strategy, broker: Broker, data: Sequence[Candle], symbol: str):

        self._results = None
        self._strategy: Strategy = strategy
        self._broker = broker
        self._data = data
        self._symbol = symbol

    def run(self) -> BacktestResult:
        if self._results is None:
            self._results = self._calculate_results()

        return self._results

    def _calculate_results(self) -> BacktestResult:
        curr_candles = []
        order_history = []
        records = []
        order = None

        for candle in self._data:
            if order is not None:
                order_history.append(self._execute_pending_order(order, candle))

            curr_candles.append(candle)
            signal = self._strategy.generate_signal(curr_candles)
            order = self._create_order(candle, signal)

            records.append(self._create_record(candle, signal))

        return BacktestResult(
            records=records,
            trades=self._broker.trades,
            orders=order_history
        )

    def _execute_pending_order(self, order: Order, candle: Candle) -> OrderExecution:
        try:
            self._broker.execute(order, {self._symbol: candle.open}, candle.timestamp)
            return OrderExecution(order, True, None)
        except InsufficientError as e:
            return OrderExecution(order, False, e)

    def _create_order(self, candle: Candle, signal: Signal) -> Order | None:

        if signal == Signal.BUY or signal == Signal.SELL:
            side = side_from_signal(signal)
            return Order(
                symbol=self._symbol,
                timestamp=candle.timestamp,
                quantity=self._calculate_quantity(candle.close, side),
                side=side
            )

        else:
            return None

    def _create_record(self, candle: Candle, signal: Signal) -> BacktestRecord:
        return  BacktestRecord(
            timestamp=candle.timestamp,
            signal=signal,
            portfolio_value=self._broker.portfolio.value(prices={self._symbol: candle.close}),
            cash=self._broker.portfolio.cash
        )

    def _calculate_quantity(self, price: float, side: Side) -> int:
        if price <= 0:
            raise ValueError("Positive active price is expected")

        if side == Side.BUY:
            return int(self._broker.portfolio.cash / price)
        elif side == Side.SELL:
            return self._broker.portfolio.positions.get(self._symbol, 0)
        else:
            raise ValueError("Unknown side")
