class NotEnoughCashException(Exception):
    def __init__(self, msg: str = "Not enough cash"):
        super().__init__(msg)