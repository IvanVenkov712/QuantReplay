from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from math import isfinite
from numbers import Real

from backtester.portfolio.position_sizing import SizingInstruction
from backtester.strategies.base import Signal


class Side(Enum):
    BUY = "buy"
    SELL = "sell"

def side_from_signal(signal: Signal) -> Side:
    if signal == Signal.BUY:
        return Side.BUY
    elif signal == Signal.SELL:
        return Side.SELL
    else:
        raise ValueError("Invalid signal")

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
class OrderIntent:
    symbol: str
    side: Side
    timestamp: datetime
    sizing_instruction: SizingInstruction

    def __post_init__(self) -> None:
        _validate_symbol(self.symbol)
        _validate_side(self.side)
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

def _validate_commission(commission: float) -> None:
    if not isinstance(commission, Real) or not isfinite(commission):
        raise ValueError("Price must be a finite number.")

    if commission < 0:
        raise ValueError("Commission must be non-negative.")


def _validate_timestamp(timestamp: datetime) -> None:
    if not isinstance(timestamp, datetime):
        raise ValueError("Timestamp must be a datetime.")
