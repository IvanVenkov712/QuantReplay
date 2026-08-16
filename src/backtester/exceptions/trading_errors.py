class InsufficientFundsError(Exception):
    def __init__(self, msg: str = "Not enough cash"):
        super().__init__(msg)

class InsufficientPositionError(Exception):
    pass

class ActiveNotFoundError(Exception):
    pass