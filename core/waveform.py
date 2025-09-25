import math
import random
from abc import ABC, abstractmethod

class BaseWaveformGenerator(ABC):
    @abstractmethod
    def value(self, t):
        pass

    def values(self, t_array):
        return [self.value(t) for t in t_array]

class SineGenerator(BaseWaveformGenerator):
    def __init__(self, frequency, phase=0.0):
        self.frequency = frequency
        self.phase = phase

    def value(self, t):
        return math.sin(2 * math.pi * self.frequency * t + self.phase)

class CosineGenerator(BaseWaveformGenerator):
    def __init__(self, frequency, phase=0.0):
        self.frequency = frequency
        self.phase = phase

    def value(self, t):
        return math.cos(2 * math.pi * self.frequency * t + self.phase)

class TriangleGenerator(BaseWaveformGenerator):
    def __init__(self, frequency, phase=0.0):
        self.frequency = frequency
        self.phase = phase

    def value(self, t):
        period = 1 / self.frequency
        frac = math.fmod(t + self.phase / (2 * math.pi * self.frequency), period) / period
        if frac < 0.5:
            return -1 + 4 * frac
        else:
            return 3 - 4 * frac

class SquareGenerator(BaseWaveformGenerator):
    def __init__(self, frequency, phase=0.0):
        self.frequency = frequency
        self.phase = phase

    def value(self, t):
        return math.copysign(1, math.sin(2 * math.pi * self.frequency * t + self.phase))

class StepGenerator(BaseWaveformGenerator):
    def __init__(self, frequency, phase=0.0):
        self.frequency = frequency
        self.phase = phase

    def value(self, t):
        # Simple step: alternate -1 and 1 based on frequency
        if math.sin(2 * math.pi * self.frequency * t + self.phase) > 0:
            return 1
        return -1

class NoiseGenerator(BaseWaveformGenerator):
    def __init__(self, frequency=0, phase=0):
        pass

    def value(self, t):
        return random.uniform(-1, 1)

class ConstantGenerator(BaseWaveformGenerator):
    def __init__(self, value=1.0):
        # value should be in normalized units (typically -1..1)
        self._value = float(value)

    def value(self, t):
        return self._value