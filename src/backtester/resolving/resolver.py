from dataclasses import dataclass
from datetime import datetime

from backtester.execution.costs import ExecutionCostCalculator
from backtester.domain.trading import Side, SizingMode, SizingInstruction, Order, OrderIntent


@dataclass(frozen=True)
class ResolutionContext:
    timestamp: datetime
    reference_price: float
    cash: float
    current_quantity: int
    portfolio_value: float

    def __post_init__(self):
        if self.cash < 0:
            raise ValueError("cash cannot be negative")

        if self.current_quantity < 0:
            raise ValueError("current quantity cannot be negative")

        if self.portfolio_value < self.cash:
            raise ValueError("portfolio value cannot be less than cash")

        if self.reference_price <= 0:
            raise ValueError("price must be positive")

class BuyQuantityCapper:
    def __init__(self, cost_calculator: ExecutionCostCalculator):
        self._cost_calculator: ExecutionCostCalculator = cost_calculator

    def cap(self,
            budget: float,
            reference_price: float,
            max_quantity: int | None) -> int:
        quantity = int(budget // reference_price) + 1

        if max_quantity is not None:
            quantity = min(quantity, max_quantity)

        while quantity > 0 and self._cost_calculator.estimate_buy_cost(quantity, reference_price) > budget:
            quantity -= 1

        return quantity


class QuantityResolver:
    def __init__(self, capper: BuyQuantityCapper):
        self._capper: BuyQuantityCapper = capper

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
        return self._capper.cap(budget, reference_price, max_quantity)

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
        return self._resolve_affordable_quantity(
            context.cash,
            context.reference_price,
        )

    def _resolve_buy_quantity_percent(self, percent: float, context: ResolutionContext):
        budget = context.cash * percent
        return self._resolve_affordable_quantity(budget, context.reference_price)

    def _resolve_buy_quantity_up_to(self, max_q: int, context: ResolutionContext):
        return self._resolve_affordable_quantity(
            context.cash,
            context.reference_price,
            max_q,
        )

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

class BufferQuantityResolver(QuantityResolver):
    def __init__(self, resolver: QuantityResolver, capper:BuyQuantityCapper, buffer_rate: float):
        if not 0 <= buffer_rate < 1:
            raise ValueError("buffer_rate must be float in [0, 1)")
        self._resolver = resolver
        self._capper = capper
        self._buffer_rate = buffer_rate

    def resolve_quantity(self, side: Side, instr: SizingInstruction, context: ResolutionContext) -> int:
        requested_quantity = self._resolver.resolve_quantity(side, instr, context)

        if side == Side.SELL or requested_quantity <= 0:
            return requested_quantity

        buffered_budget = context.cash * (1 - self._buffer_rate)

        return self._capper.cap(
            budget=buffered_budget,
            reference_price=context.reference_price,
            max_quantity=requested_quantity,
        )

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



