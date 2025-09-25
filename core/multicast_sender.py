import socket
import time

class MulticastSender:
    def __init__(self, group, port, ttl=1, interface='0.0.0.0'):
        self.group = group
        self.port = port
        self.ttl = ttl
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, bytes([ttl]))
        # Additional interface setup if needed

    def send_packets(self, packets, inter_packet_delay_ms=0):
        for p in packets:
            self.sock.sendto(p, (self.group, self.port))
            if inter_packet_delay_ms > 0:
                time.sleep(inter_packet_delay_ms / 1000.0)

    def close(self):
        self.sock.close()