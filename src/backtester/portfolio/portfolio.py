from backtester.portfolio.position import Position


class Portfolio:
    __cash: float
    __positions: set[Position]

    def __init__(self, cash: float):
        self.__cash = cash
        self.__positions = set()

    @property
    def cash(self):
        return self.__cash

    @property
    def positions(self):
        return self.__positions

    def value(self, prices: dict[str, float]) -> float:
        return self.cash + sum(prices[pos.symbol] *  pos.count for pos in self.positions)