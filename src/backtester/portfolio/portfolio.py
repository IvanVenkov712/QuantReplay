from dataclasses import dataclass

@dataclass
class Portfolio:
    cash: float
    positions: dict[str, int]

    def value(self, prices: dict[str, float]) -> float:
        return self.cash + sum(
            prices[symbol] *  quantity for symbol, quantity in self.positions.items()
        )
