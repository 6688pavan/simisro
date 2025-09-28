import math
import random

def make_waveform(waveform_type, freq, phase, full_sweep):
    class BaseWaveform:
        def value(self, t, min_v, max_v):
            norm = self._compute(t)  # Returns [-1, 1]
            return min_v + (max_v - min_v) * (norm + 1) / 2

    class Sine(BaseWaveform):
        def _compute(self, t):
            return math.sin(2 * math.pi * freq * t + phase)

    class Triangle(BaseWaveform):
        def _compute(self, t):
            period = 1 / freq
            frac = math.fmod(t + phase / (2 * math.pi), period) / period
            return -1 + 4 * frac if frac < 0.5 else 3 - 4 * frac

    class Square(BaseWaveform):
        def _compute(self, t):
            return math.copysign(1, math.sin(2 * math.pi * freq * t + phase))

    class Step(BaseWaveform):
        def _compute(self, t):
            return 1 if math.sin(2 * math.pi * freq * t + phase) > 0 else -1

    class Noise(BaseWaveform):
        def _compute(self, t):
            return random.uniform(-1, 1)

    return {
        "Sine": Sine,
        "Triangle": Triangle,
        "Square": Square,
        "Step": Step,
        "Noise": Noise
    }.get(waveform_type, Sine)()