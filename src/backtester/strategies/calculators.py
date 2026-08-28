from abc import ABC, abstractmethod
from collections import deque
from math import isclose
from typing import Callable, Self


class Calculator(ABC):
    @abstractmethod
    def next_value(self, value: float) -> float | None:
        pass

    @abstractmethod
    def reset(self):
        pass


class MovingAverageCalculator(Calculator, ABC):
    def __init__(self, window_size):
        if not (isinstance(window_size, int) and not isinstance(window_size, bool) and window_size > 0):
            raise ValueError("positive integer is expected for window size")

        self._window_size = window_size

    @property
    def window_size(self) -> int:
        return self._window_size


class SimpleMovingAverageCalculator(MovingAverageCalculator):

    def __init__(self, window_size: int):
        super().__init__(window_size)
        self._window = deque(maxlen=window_size)
        self._sum: float = 0.0

    def next_value(self, value: float) -> float | None:
        self._update_state(value)
        if len(self._window) >= self.window_size:
            return self._sum / self.window_size

        return None

    def _update_state(self, value: float):
        if len(self._window) >= self.window_size:
            self._sum -= self._window.popleft()

        self._sum += value
        self._window.append(value)

    def reset(self):
        self._window.clear()
        self._sum = 0.0


class ExponentialMovingAverageCalculator(MovingAverageCalculator):
    def __init__(self, window_size: int, *, alpha: float):
        super().__init__(window_size)
        if not 0 < alpha < 1:
            raise ValueError("alpha must be in (0, 1)")
        self._window = deque(maxlen=window_size)
        self._filled = False
        self._curr: float | None = None
        self._alpha = alpha

    def next_value(self, value: float) -> float | None:
        self._update_state(value)
        return self._curr

    def _update_state(self, value: float):
        if self._filled:
            self._curr = value * self._alpha + self._curr * (1 - self._alpha)
        else:
            self._window.append(value)
            if len(self._window) == self.window_size:
                self._curr = sum(self._window) / self.window_size
                self._filled = True
                self._window.clear()

    def reset(self):
        self._window.clear()
        self._filled = False
        self._curr = None

    @classmethod
    def standard(cls, n: int) -> Self:
        if not (isinstance(n, int) and not isinstance(n, bool) and n > 0):
            raise ValueError("positive integer is expected for window size")

        return cls(
            n, alpha=2.0 / (n + 1)
        )

    @classmethod
    def wilder(cls, n: int) -> Self:
        if not (isinstance(n, int) and not isinstance(n, bool) and n > 0):
            raise ValueError("positive integer is expected for window size")

        return cls(
            n, alpha=1.0 / n
        )


class RSICalculator(Calculator):
    def __init__(self,
                 factory: Callable[[int], MovingAverageCalculator],
                 window_size: int = 14
                 ):

        if not (isinstance(window_size, int) and not isinstance(window_size, bool) and window_size > 1):
            raise ValueError("positive integer is expected for window size")

        self._u_calc = factory(window_size)
        self._d_calc = factory(window_size)
        self._prev_value: float | None = None

    def next_value(self, value: float) -> float | None:
        if self._prev_value is None:
            self._prev_value = value
            return None

        delta = value - self._prev_value
        self._prev_value = value
        u_move = max(0, delta)
        d_move = max(0, -delta)
        avg_u = self._u_calc.next_value(u_move)
        avg_d = self._d_calc.next_value(d_move)

        if avg_u is None or avg_d is None:
            return None

        if isclose(avg_d, 0):
            if isclose(avg_u, 0):
                return 50
            return 100
        rs = avg_u / avg_d
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def reset(self):
        self._prev_value = None
        self._u_calc.reset()
        self._d_calc.reset()


class CutlerRSICalculator(RSICalculator):
    def __init__(self, window_size: int = 14):
        super().__init__(
            lambda size: SimpleMovingAverageCalculator(size),
            window_size
        )

class ExponentialRSICalculator(RSICalculator):
    def __init__(self, window_size: int = 14, smoothing = 2):
        super().__init__(
            ExponentialMovingAverageCalculator.standard,
            window_size
        )

class WilderRSICalculator(RSICalculator):
    def __init__(self, window_size: int = 14):
        super().__init__(
            ExponentialMovingAverageCalculator.wilder,
            window_size
        )