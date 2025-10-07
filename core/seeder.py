from .packet_buffer import PacketBuffer
from .waveform import make_waveform
import math
from PyQt5.QtCore import QObject, pyqtSignal

class SeedingEngine(QObject):
    sample_generated = pyqtSignal(str, object, float)  # param_name, value(s), time
    
    def __init__(self, packet_length=1400, packets_per_record=10, time_field_offset=24):
        super().__init__()
        self.packet_length = packet_length
        self.packets_per_record = packets_per_record
        self.time_field_offset = time_field_offset

    def seed_record(self, params, record_time, dat_buffer=None, time_increment=1.0):
        buffer = PacketBuffer(self.packet_length, self.packets_per_record, self.time_field_offset)
        if dat_buffer is not None:
            # Split dat_buffer into packets (1400 bytes each)
            packets = []
            for i in range(self.packets_per_record):
                start_idx = i * self.packet_length
                end_idx = start_idx + self.packet_length
                if start_idx < len(dat_buffer):
                    packet_data = dat_buffer[start_idx:end_idx]
                    # Pad with zeros if packet is shorter than expected
                    if len(packet_data) < self.packet_length:
                        packet_data += b'\x00' * (self.packet_length - len(packet_data))
                    packets.append(bytearray(packet_data))
                else:
                    # Create empty packet if dat_buffer is too short
                    packets.append(bytearray(self.packet_length))
            buffer.buffers = packets
        else:
            buffer.reset()  # Use empty buffers when no .dat file is loaded
        buffer.set_record_time(record_time)  # Write timer to all packets

        for param in params:
            if not param.enabled or record_time < param.start_time or record_time > param.end_time:
                continue
            if param.samples_per_500ms == 1:  # Major cycle
                # Sample strictly at record_time (no phase offset)
                sample_time = record_time
                if param.dtype == "float":
                    wf = make_waveform(param.waveform, param.freq, param.phase, param.full_sweep)
                    # Use waveform value at sample_time; fall back to fixed_value if explicitly set
                    value = param.fixed_value if param.fixed_value is not None else wf.value(sample_time, param.min_v, param.max_v)
                    buffer.insert_float(param.packet_id, param.offset, value)
                    if param.enabled_in_graph:
                        self.sample_generated.emit(param.name, value, record_time)
                else:  # Digital (bit) -> toggle strictly between min_v and max_v using waveform threshold
                    wf = make_waveform(param.waveform, param.freq, param.phase, param.full_sweep)
                    analog = wf.value(sample_time, param.min_v, param.max_v)
                    threshold = (param.min_v + param.max_v) / 2.0
                    value = param.min_v if analog < threshold else param.max_v
                    if param.bit_width == 8:
                        buffer.insert_uint8(param.packet_id, param.offset, int(value))
                    elif param.bit_width == 16:
                        buffer.insert_uint16(param.packet_id, param.offset, int(value))
                    else:  # 32 bits
                        buffer.insert_uint32(param.packet_id, param.offset, int(value))
                    if param.enabled_in_graph:
                        self.sample_generated.emit(param.name, value, record_time)
            else:  # Minor cycle (5 samples)
                wf = make_waveform(param.waveform, param.freq, param.phase, param.full_sweep)
                sample_values = []
                sample_spacing = time_increment / 5.0  # Spread 5 samples across the time increment
                for i in range(5):
                    # Deterministic non-repeating time adjustment independent of ΔT (tied to waveform period):
                    # add a small phase-based time offset (~1% of the waveform period) using golden-ratio progression
                    k = int(round(record_time / time_increment)) if time_increment > 0 else 0
                    golden_frac = (k * 0.61803398875) % 1.0
                    period = 1.0 / param.freq if getattr(param, 'freq', 0.0) not in (0.0, None) else 0.0
                    phase_time_offset = (period * 0.01) * (golden_frac - 0.5) if period > 0.0 else 0.0
                    sample_time = record_time + i * sample_spacing + phase_time_offset
                    if param.dtype == "float":
                        value = wf.value(sample_time, param.min_v, param.max_v)
                        sample_values.append(value)
                        offset = param.offset + (i * 4)
                        buffer.insert_float(param.packet_id, offset, value)
                    else:
                        # Digital minor: still toggle min/max discretely at each sub-sample
                        analog = wf.value(sample_time, param.min_v, param.max_v)
                        threshold = (param.min_v + param.max_v) / 2.0
                        value = param.min_v if analog < threshold else param.max_v
                        sample_values.append(value)
                        offset = param.offset + (i * 8)
                        buffer.insert_uint64(param.packet_id, offset, int(value) & 0xFF)
                if param.enabled_in_graph:
                    self.sample_generated.emit(param.name, sample_values, record_time)
        return buffer