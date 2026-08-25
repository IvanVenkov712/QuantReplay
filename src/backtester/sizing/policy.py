from dataclasses import dataclass

from backtester.domain.trading import SizingInstruction, Side


@dataclass(frozen=True)
class SizingPlan:
    buy: SizingInstruction
    sell: SizingInstruction

    def instruction_for(self, side: Side) -> SizingInstruction:
        if side == Side.BUY:
            return self.buy
        elif side == Side.SELL:
            return self.sell
        else:
            raise ValueError("invalid side")