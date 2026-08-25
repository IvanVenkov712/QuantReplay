from backtester.engine.broker import CommissionModel
from backtester.engine.execution import ExecutionModel
from backtester.portfolio.trade import Side


class ExecutionCostEstimator:
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



class OrderResolver:
    def __init__(self, estimator: ExecutionCostEstimator):
        self._estimator: ExecutionCostEstimator = estimator

