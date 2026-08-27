from abc import ABC, abstractmethod
from collections import deque


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

class SimpleMovingAverage(MovingAverageCalculator):

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

class ExponentialMovingAverage(MovingAverageCalculator):
    def __init__(self, window_size: int, smoothing: float = 2):
        super().__init__(window_size)
        if not 0 < smoothing < window_size + 1:
            raise ValueError("smoothing must be in (0, window_size + 1)")
        self._window = deque(maxlen=window_size)
        self._filled = False
        self._curr: float | None= None
        self._factor = smoothing / (1 + self.window_size)

    def next_value(self, value: float) -> float | None:
        self._update_state(value)
        return self._curr

    def _update_state(self, value: float):
        if self._filled:
            self._curr = value * self._factor + self._curr * (1 - self._factor)
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