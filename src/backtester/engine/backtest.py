from typing import Sequence

from backtester.data.models import Candle
from backtester.engine.backtest_result import BacktestResult, OrderExecution, BacktestRecord
from backtester.engine.broker import Broker
from backtester.exceptions.trading_errors import InsufficientError
from backtester.portfolio.trade import Order, side_from_signal, Side
from backtester.strategies.base import Strategy, Signal
from backtester.portfolio.position_sizing import SizingContext, PositionSizer


class BacktestEngine:
    """Run a single-symbol backtest with explicit next-candle execution.

    The engine feeds the strategy only the candles available up to the current
    point in time. A signal generated from candle T may create a pending order,
    but that order is executed at candle T+1 open. This keeps the close used for
    signal generation separate from the execution price and avoids look-ahead
    bias.
    """

    def __init__(
            self,
            strategy: Strategy,
            broker: Broker,
            sizer: PositionSizer,
            data: Sequence[Candle],
            symbol: str
    ):
        """Create a backtest engine for one strategy, broker, data set, and symbol.

        Args:
            strategy: Trading strategy that converts available candle history
                into a buy, sell, or hold signal.
            broker: Broker responsible for order execution and portfolio
                accounting.
            data: Chronologically ordered candles used by the simulation.
            symbol: Asset symbol traded by this engine.
        """

        self._results = None
        self._strategy: Strategy = strategy
        self._broker = broker
        self._sizer = sizer
        self._data = data
        self._symbol = symbol

    def run(self) -> BacktestResult:
        """Run the backtest once and return the cached result on later calls."""
        if self._results is None:
            self._results = self._calculate_results()

        return self._results

    def _calculate_results(self) -> BacktestResult:
        """Iterate through candles, execute pending orders, and record results.

        For each candle, any order created by the previous candle's signal is
        executed first at the current open. The current candle is then added to
        the strategy's available history, a new signal is generated, and the
        portfolio is valued at the current close.
        """
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
        """Execute a pending order at the current candle open.

        Returns an OrderExecution describing whether the broker accepted the
        order. Insufficient cash or position is captured in the result instead
        of stopping the whole backtest.
        """
        try:
            self._broker.execute(order, {self._symbol: candle.open}, candle.timestamp)
            return OrderExecution(order, True, None)
        except InsufficientError as e:
            return OrderExecution(order, False, e)

    def _create_order(self, candle: Candle, signal: Signal) -> Order | None:
        """Convert a buy or sell signal into an order timestamped at signal time.

        The quantity is calculated from the current close because that is the
        latest price known when the signal is generated. Execution still happens
        later, at the next candle open.
        """

        if signal == Signal.BUY or signal == Signal.SELL:
            side = side_from_signal(signal)
            quantity = self._calculate_quantity(candle.close, side)

            if quantity <= 0:
                return None

            return Order(
                symbol=self._symbol,
                timestamp=candle.timestamp,
                quantity=quantity,
                side=side
            )

        else:
            return None

    def _create_record(self, candle: Candle, signal: Signal) -> BacktestRecord:
        """Create a per-candle snapshot valued at the current close."""
        return  BacktestRecord(
            timestamp=candle.timestamp,
            generated_signal=signal,
            portfolio_value_at_close=self._broker.portfolio.value(prices={self._symbol: candle.close}),
            cash=self._broker.portfolio.cash
        )

    def _calculate_quantity(self, price: float, side: Side) -> int:
        return self._sizer.calculate_size(self._create_context(price), side)
        # if price <= 0:
        #     raise ValueError("Positive active price is expected")
        #
        # if side == Side.BUY:
        #     return int(self._broker.portfolio.cash / price)
        # elif side == Side.SELL:
        #     return self._broker.portfolio.position_quantity(self._symbol)
        # else:
        #     raise ValueError("Unknown side")

    def _create_context(self, price: float) -> SizingContext:
        current_quantity = self._broker.portfolio.position_quantity(self._symbol)
        cash = self._broker.portfolio.cash
        return SizingContext(
            cash=cash,
            current_quantity=current_quantity,
            price=price,
            portfolio_value=cash + current_quantity * price
        )
