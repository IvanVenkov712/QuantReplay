from dataclasses import dataclass
from datetime import datetime

from backtester.engine.broker import CommissionModel
from backtester.engine.execution import ExecutionModel
from backtester.portfolio.portfolio import Portfolio
from backtester.portfolio.position_sizing import SizingInstruction, SizingMode
from backtester.portfolio.trade import Side, OrderIntent, Order


class ExecutionCostEstimator:
    def __init__(self, execution_model: ExecutionModel, commission_model: CommissionModel):
        self._execution_model: ExecutionModel = execution_model
        self._commission_model: CommissionModel = commission_model

    def estimate_buy_cost(self, quantity: int, reference_price: float) -> float:
        fill_price = self._execution_model.calculate_fill_price(reference_price, Side.BUY)
        commission = self._commission_model.calculate(quantity, fill_price)
        return quantity * fill_price + commission

    def estimate_sell_cost(self, quantity: int, reference_price: float) -> float:
        fill_price = self._execution_model.calculate_fill_price(reference_price,Side.SELL)
        commission = self._commission_model.calculate(quantity, fill_price)
        return commission

@dataclass(frozen=True)
class ResolutionContext:
    timestamp: datetime
    reference_price: float
    cash: float
    current_quantity: int
    portfolio_value: float

class QuantityResolver:
    def __init__(self, estimator: ExecutionCostEstimator):
        self._estimator: ExecutionCostEstimator = estimator

    def resolve_quantity(self, side: Side, instr: SizingInstruction, context: ResolutionContext) -> int:
        if side == Side.BUY:
            return self._resolve_buy_quantity(instr, context)
        elif side == Side.SELL:
            return self._resolve_sell_quantity(instr, context)
        else:
            raise ValueError("invalid side")

    def _resolve_affordable_quantity(
            self,
            budget: float,
            reference_price: float,
            max_quantity: int | None = None,
    ) -> int:
        quantity = int(budget // reference_price)

        if max_quantity is not None:
            quantity = min(quantity, max_quantity)

        while quantity > 0 and self._estimator.estimate_buy_cost(quantity, reference_price) > budget:
            quantity -= 1

        return quantity

    def _resolve_buy_quantity(self, instruction: SizingInstruction, context: ResolutionContext) -> int:
        if instruction.mode == SizingMode.ALL_IN:
            return self._resolve_buy_quantity_all_in(context)
        elif instruction.mode == SizingMode.PERCENT:
            return self._resolve_buy_quantity_percent(instruction.value, context)
        elif instruction.mode == SizingMode.UP_TO:
            return self._resolve_buy_quantity_up_to(instruction.value, context)
        elif instruction.mode == SizingMode.FIXED:
            return instruction.value
        else:
            raise ValueError("Invalid sizing instruction")

    def _resolve_buy_quantity_all_in(self, context: ResolutionContext) -> int:
        return self._resolve_affordable_quantity(context.cash, context.reference_price)

    def _resolve_buy_quantity_percent(self, percent: float, context: ResolutionContext):
        return self._resolve_affordable_quantity(context.cash * percent, context.reference_price)

    def _resolve_buy_quantity_up_to(self, max_q: int, context: ResolutionContext):
        return self._resolve_affordable_quantity(context.cash, context.reference_price, max_q)

    def _resolve_sell_quantity(self, instruction: SizingInstruction, context: ResolutionContext) -> int:
        if instruction.mode == SizingMode.FIXED:
            return instruction.value
        elif instruction.mode == SizingMode.ALL_IN:
            return context.current_quantity
        elif instruction.mode == SizingMode.UP_TO:
            return min(instruction.value, context.current_quantity)
        elif instruction.mode == SizingMode.PERCENT:
            return int(context.current_quantity * instruction.value)
        else:
            raise ValueError("Invalid sizing instruction")

class OrderResolver:
    def __init__(self, q_resolver: QuantityResolver):
        self._q_resolver: QuantityResolver = q_resolver

    def resolve(self, intent: OrderIntent, context: ResolutionContext) -> Order | None:
        quantity = self._q_resolver.resolve_quantity(intent.side, intent.sizing_instruction, context)
        if quantity <= 0:
            return None

        return Order(
            symbol=intent.symbol,
            side = intent.side,
            timestamp=context.timestamp,
            quantity=quantity
        )



