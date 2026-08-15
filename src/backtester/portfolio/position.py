class Position:
    __symbol: str
    __count: int

    def __init__(self, symbol: str, count: int = 0):
        self.__symbol = symbol
        self.__count = count

    @property
    def symbol(self):
        return self.__symbol

    @property
    def count(self):
        return self.__count

    @count.setter
    def count(self, count: int):
        self.__count = count


    def __eq__(self, other):
        if not isinstance(other, Position):
            return False

        return self.symbol == other.symbol

    def __hash__(self):
        return hash(self.__symbol)