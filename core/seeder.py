from .packet_buffer import PacketBuffer
from .waveform import make_waveform
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
                if param.dtype == "float":
                    # For float major, keep fixed value behavior if provided, else 0.0
                    value = param.fixed_value if param.fixed_value is not None else 0.0
                    buffer.insert_float(param.packet_id, param.offset, value)
                    if param.enabled_in_graph:
                        self.sample_generated.emit(param.name, value, record_time)
                else:  # Digital (bit) -> toggle strictly between min_v and max_v using waveform threshold
                    wf = make_waveform(param.waveform, param.freq, param.phase, param.full_sweep)
                    analog = wf.value(record_time, param.min_v, param.max_v)
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
                    sample_time = record_time + i * sample_spacing
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