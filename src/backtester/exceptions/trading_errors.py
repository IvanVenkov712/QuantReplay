"""Exceptions raised when an order cannot be executed."""

class InsufficientError(Exception):
    """Base class for orders rejected due to insufficient resources."""

    pass

class InsufficientFundsError(InsufficientError):
    """Raised when cash cannot cover an order and its commission."""

    def __init__(self, msg: str = "Not enough cash"):
        super().__init__(msg)

class InsufficientPositionError(InsufficientError):
    """Raised when a sell order exceeds the owned position."""

    pass

class PriceNotFoundError(Exception):
    """Raised when no reference price is supplied for an order symbol."""

    pass
