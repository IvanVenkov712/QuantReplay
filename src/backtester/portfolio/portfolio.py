class Portfolio:
    __cash: float
    __positions: dict[str, int]

    def __init__(self, cash: float):
        self.__cash = cash
        self.__positions = {}

    @property
    def cash(self) -> float:
        return self.__cash

    @property
    def positions(self) -> dict[str, int]:
        return self.__positions.copy()

    def buy(self, symbol: str, count: int, price: float) -> None:
        if count <= 0:
            raise ValueError("Count must be positive.")

        if price <= 0:
            raise ValueError("Price must be positive.")

        cost = count * price

        if cost > self.__cash:
            raise ValueError("Insufficient cash.")

        self.__cash -= cost
        self.__positions[symbol] = self.__positions.get(symbol, 0) + count

    def sell(self, symbol: str, count: int, price: float) -> None:
        if count <= 0:
            raise ValueError("Count must be positive.")

        if price <= 0:
            raise ValueError("Price must be positive.")

        owned = self.__positions.get(symbol, 0)

        if count > owned:
            raise ValueError("Insufficient position.")

        self.__cash += count * price
        remaining = owned - count

        if remaining == 0:
            del self.__positions[symbol]
        else:
            self.__positions[symbol] = remaining

    def value(self, prices: dict[str, float]) -> float:
        return self.cash + sum(
            prices[symbol] *  count for symbol, count in self.__positions.items()
        )
