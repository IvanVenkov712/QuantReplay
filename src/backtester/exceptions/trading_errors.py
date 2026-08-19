class InsufficientError(Exception):
    pass

class InsufficientFundsError(InsufficientError):
    def __init__(self, msg: str = "Not enough cash"):
        super().__init__(msg)

class InsufficientPositionError(InsufficientError):
    pass

class PriceNotFoundError(Exception):
    pass