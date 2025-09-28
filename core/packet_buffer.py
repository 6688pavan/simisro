import struct

class PacketBuffer:
    def __init__(self, packet_length=1400, packets_per_record=10, time_field_offset=24):
        self.packet_length = int(packet_length)
        if self.packet_length % 4 != 0:
            self.packet_length += (4 - self.packet_length % 4)
        self.packets_per_record = int(packets_per_record)
        self.time_field_offset = int(time_field_offset)
        self.reset()

    def reset(self):
        self.buffers = [bytearray(self.packet_length) for _ in range(self.packets_per_record)]

    def insert_float(self, packet_id, offset, value):
        if 0 <= packet_id < self.packets_per_record and offset + 4 <= self.packet_length:
            self.buffers[packet_id][offset:offset+4] = struct.pack('<f', float(value))
            return True
        return False

    def insert_uint8(self, packet_id, offset, value):
        if 0 <= packet_id < self.packets_per_record and offset < self.packet_length:
            self.buffers[packet_id][offset] = value & 0xFF
            return True
        return False

    def insert_uint16(self, packet_id, offset, value):
        if 0 <= packet_id < self.packets_per_record and offset + 2 <= self.packet_length:
            self.buffers[packet_id][offset:offset+2] = struct.pack('<H', value & 0xFFFF)
            return True
        return False

    def insert_uint32(self, packet_id, offset, value):
        if 0 <= packet_id < self.packets_per_record and offset + 4 <= self.packet_length:
            self.buffers[packet_id][offset:offset+4] = struct.pack('<I', value & 0xFFFFFFFF)
            return True
        return False

    def insert_uint64(self, packet_id, offset, value):
        if 0 <= packet_id < self.packets_per_record and offset + 8 <= self.packet_length:
            self.buffers[packet_id][offset:offset+8] = struct.pack('<Q', value & 0xFF)
            return True
        return False

    def set_record_time(self, record_time):
        b = struct.pack('<f', float(record_time))
        for buf in self.buffers:
            if self.time_field_offset + 4 <= self.packet_length:
                buf[self.time_field_offset:self.time_field_offset+4] = b

    def get_packets(self):
        return [bytes(b) for b in self.buffers]