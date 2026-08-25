from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from math import isfinite
from numbers import Real

class Signal(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

class Side(Enum):
    BUY = "buy"
    SELL = "sell"

class SizingMode(Enum):
    FIXED = auto()
    PERCENT = auto()
    ALL_IN = auto()
    UP_TO = auto()

@dataclass(frozen=True)
class SizingInstruction:
    value: int | float | None
    mode: SizingMode

    def __post_init__(self):
        if self.mode == SizingMode.FIXED or self.mode == SizingMode.UP_TO:
            _validate_quantity(self.value)
        elif self.mode == SizingMode.PERCENT:
            _validate_percent(self.value)
        elif self.mode == SizingMode.ALL_IN:
            if self.value is not None:
                raise ValueError("With all in value should be none")
        else:
            raise ValueError("correct sizing mode expected")

@dataclass(frozen=True)
class OrderIntent:
    symbol: str
    side: Side
    timestamp: datetime
    sizing_instruction: SizingInstruction

    def __post_init__(self) -> None:
        _validate_symbol(self.symbol)
        _validate_side(self.side)
        _validate_timestamp(self.timestamp)

@dataclass(frozen=True)
class Order:
    symbol: str
    side: Side
    quantity: int
    timestamp: datetime

    def __post_init__(self) -> None:
        _validate_symbol(self.symbol)
        _validate_side(self.side)
        _validate_quantity(self.quantity)
        _validate_timestamp(self.timestamp)

@dataclass(frozen=True)
class Trade:
    symbol: str
    side: Side
    quantity: int
    fill_price: float
    commission: float
    timestamp: datetime

    def __post_init__(self) -> None:
        _validate_symbol(self.symbol)
        _validate_side(self.side)
        _validate_quantity(self.quantity)
        _validate_price(self.fill_price)
        _validate_commission(self.commission)
        _validate_timestamp(self.timestamp)

def _validate_symbol(symbol: str) -> None:
    if not isinstance(symbol, str) or not symbol:
        raise ValueError("Symbol must be a non-empty string.")


def _validate_side(side: Side) -> None:
    if not isinstance(side, Side):
        raise ValueError("Side must be a Side.")

def _validate_quantity(quantity: int) -> None:
    if not isinstance(quantity, int) or isinstance(quantity, bool):
        raise ValueError("Quantity must be an integer.")

    if quantity <= 0:
        raise ValueError("Quantity must be positive.")

def _validate_quantity_instruction(instr: float) -> None:
    if not isinstance(instr, float):
        raise ValueError("The instruction must be a float")

    if not 0 <= instr <= 1:
        raise ValueError("The instruction muse be between 0 and 1")


def _validate_price(price: float) -> None:
    if not isinstance(price, Real) or not isfinite(price):
        raise ValueError("Price must be a finite number.")

    if price <= 0:
        raise ValueError("Price must be positive.")

def _validate_percent(value):
    if not (isinstance(value, float | int) and 0 <= value <= 1):
        raise ValueError("value must be in [0, 1]")

def _validate_commission(commission: float) -> None:
    if not isinstance(commission, Real) or not isfinite(commission):
        raise ValueError("Price must be a finite number.")

    if commission < 0:
        raise ValueError("Commission must be non-negative.")


def _validate_timestamp(timestamp: datetime) -> None:
    if not isinstance(timestamp, datetime):
        raise ValueError("Timestamp must be a datetime.")
