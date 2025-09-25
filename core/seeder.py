from .packet_buffer import PacketBuffer
from .waveform import *

class SeedingEngine:
    def __init__(self, parameter_list, record_spec, signals=None):
        self.parameter_list = parameter_list
        self.record_spec = record_spec
        self.signals = signals
        self.waveform_generators = self._create_generators()

    def _create_generators(self):
        generators = {}
        for p in self.parameter_list.parameters:
            settings = p.waveform_settings
            # Create generator using a case-insensitive type match and defaults
            w_type = str(settings.get('type', 'sine')).strip().lower()
            freq = settings.get('frequency', 1.0)
            phase = settings.get('phase', 0.0)
            if w_type in ('sine', 'sin'):
                gen = SineGenerator(freq, phase)
            elif w_type in ('cosine', 'cos'):
                gen = CosineGenerator(freq, phase)
            elif w_type in ('triangle', 'tri'):
                gen = TriangleGenerator(freq, phase)
            elif w_type in ('square', 'sqr'):
                gen = SquareGenerator(freq, phase)
            elif w_type in ('step', 'stepper'):
                gen = StepGenerator(freq, phase)
            elif w_type in ('noise', 'random'):
                gen = NoiseGenerator()
            elif w_type in ('constant', 'const'):
                # constant uses the 'amplitude' or 'offset' field; use amplitude as normalized value
                const_val = settings.get('amplitude', settings.get('offset', 1.0))
                # map to normalized range expected by waveform (we keep as-is)
                from .waveform import ConstantGenerator
                gen = ConstantGenerator(const_val)
            else:
                # Fallback to a sine generator and log via raising so caller may handle
                raise ValueError(f"Unknown waveform type: {settings.get('type')}")
            generators[p.name] = gen
        return generators

    def _create_generator_for_param(self, p):
        """Create and return a waveform generator for parameter p (robust to case differences)."""
        settings = p.waveform_settings or {}
        w_type = str(settings.get('type', 'sine')).strip().lower()
        freq = settings.get('frequency', 1.0)
        phase = settings.get('phase', 0.0)
        if w_type in ('sine', 'sin'):
            return SineGenerator(freq, phase)
        if w_type in ('cosine', 'cos'):
            return CosineGenerator(freq, phase)
        if w_type in ('triangle', 'tri'):
            return TriangleGenerator(freq, phase)
        if w_type in ('square', 'sqr'):
            return SquareGenerator(freq, phase)
        if w_type in ('step', 'stepper'):
            return StepGenerator(freq, phase)
        if w_type in ('noise', 'random'):
            return NoiseGenerator()
        if w_type in ('constant', 'const'):
            from .waveform import ConstantGenerator
            const_val = settings.get('amplitude', settings.get('offset', 1.0))
            return ConstantGenerator(const_val)
        # Default fallback
        return SineGenerator(freq, phase)

    def seed_record(self, record_time):
        buffer = PacketBuffer(self.record_spec.packets_per_record, self.record_spec.packet_length)
        for p in self.parameter_list.parameters:
            N = p.samples_per_500ms
            delta = 0.5 / N if N > 0 else 0
            t_array = [record_time + i * delta for i in range(N)]
            gen = self.waveform_generators.get(p.name)
            if gen is None:
                # Lazily create generator for newly-loaded parameters
                gen = self._create_generator_for_param(p)
                self.waveform_generators[p.name] = gen
            normalized = gen.values(t_array)
            for i, norm in enumerate(normalized):
                # Determine amplitude and offset so the waveform is centered between min_val and max_val
                if p.full_sweep:
                    amplitude = (p.max_val - p.min_val) / 2.0
                    offset_val = (p.max_val + p.min_val) / 2.0
                else:
                    # Use provided waveform settings but ensure resulting wave sits between min and max
                    amplitude = float(p.waveform_settings.get('amplitude', 1.0))
                    offset_val = float(p.waveform_settings.get('offset', 0.0))
                    # If amplitude/offset would push values outside [min_val, max_val], recenter
                    max_possible = offset_val + amplitude
                    min_possible = offset_val - amplitude
                    if max_possible > p.max_val or min_possible < p.min_val:
                        # recompute amplitude as half-range and center
                        amplitude = (p.max_val - p.min_val) / 2.0
                        offset_val = (p.max_val + p.min_val) / 2.0
                value = offset_val + amplitude * norm
                value = max(p.min_val, min(p.max_val, value))
                curr_offset = p.offset + i * (4 if p.dtype == 'float' else 1)
                sample_time = t_array[i]
                if self.signals:
                    self.signals.sample_generated.emit(p.name, sample_time, value)
                if p.dtype == 'float':
                    buffer.insert_float(p.packet_id, curr_offset, value)
                elif p.dtype == 'bit':
                    buffer.insert_bit(p.packet_id, curr_offset, value > 0)
        buffer.set_time_field(record_time, self.record_spec.timestamp_packet_id, self.record_spec.timestamp_offset)
        return buffer