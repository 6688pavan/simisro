import struct

class PacketBuffer:
    def __init__(self, packets_per_record, packet_length):
        self.packets_per_record = packets_per_record
        self.packet_length = packet_length
        self.packets = [bytearray(packet_length) for _ in range(packets_per_record)]

    def insert_float(self, packet_id, offset, float_val):
        if packet_id >= self.packets_per_record or offset + 4 > self.packet_length:
            raise ValueError("Invalid packet_id or offset overflow")
        self.packets[packet_id][offset:offset + 4] = struct.pack('>f', float_val)

    def insert_bit(self, packet_id, offset, boolean):
        if packet_id >= self.packets_per_record or offset >= self.packet_length:
            raise ValueError("Invalid packet_id or offset")
        self.packets[packet_id][offset] = 1 if boolean else 0

    def set_time_field(self, record_time, timestamp_packet_id, timestamp_offset):
        self.insert_float(timestamp_packet_id, timestamp_offset, record_time)

    def get_packets(self):
        return [bytes(p) for p in self.packets]