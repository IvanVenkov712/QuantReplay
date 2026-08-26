from abc import ABC, abstractmethod

from backtester.domain.trading import Side


class ExecutionModel:
    def __init__(self, slippage_rate: float):
        if not 0 <= slippage_rate < 1:
            raise ValueError("slippage_rate must be in [0, 1)")

        self._slippage_rate = slippage_rate

    def calculate_fill_price(self, reference_price: float, side: Side) -> float:
        if reference_price <= 0:
            raise ValueError("reference_price must be positive")

        if side == Side.BUY:
            return reference_price * (1 + self._slippage_rate)
        elif side == Side.SELL:
            return reference_price * (1 - self._slippage_rate)
        else:
            raise ValueError("Unknown side")

class CommissionModel(ABC):
    @abstractmethod
    def calculate(self, quantity: int, fill_price: float) -> float:
        pass


class NoCommissionModel(CommissionModel):
    def calculate(self, quantity: int, fill_price: float) -> float:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if fill_price <= 0:
            raise ValueError("fill_price must be positive")
        return 0.0


class FixedCommissionModel(CommissionModel):
    _commission: float

    def __init__(self, commission: float):
        if commission < 0:
            raise ValueError("Non-negative commission is required")
        self._commission = commission

    def calculate(self, quantity: int, fill_price: float) -> float:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if fill_price <= 0:
            raise ValueError("fill_price must be positive")
        return self._commission


class ProportionalCommissionModel(CommissionModel):
    _percent: float
    def __init__(self, percent: float):
        if not 0 <= percent <= 1:
            raise ValueError("percent must be between 0 and 1")
        self._percent = percent

    def calculate(self, quantity: int, fill_price: float) -> float:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if fill_price <= 0:
            raise ValueError("fill_price must be positive")
        return quantity * fill_price * self._percent


class ExecutionCostCalculator:
    def __init__(self, execution_model: ExecutionModel, commission_model: CommissionModel):
        self._execution_model: ExecutionModel = execution_model
        self._commission_model: CommissionModel = commission_model

    def estimate_buy_cost(self, quantity: int, reference_price: float) -> float:
        fill_price = self._execution_model.calculate_fill_price(reference_price, Side.BUY)
        commission = self._commission_model.calculate(quantity, fill_price)
        return quantity * fill_price + commission

    def estimate_sell_cost(self, quantity: int, reference_price: float) -> float:
        fill_price = self._execution_model.calculate_fill_price(reference_price,Side.SELL)
        commission = self._commission_model.calculate(quantity, fill_price)
        return commission
