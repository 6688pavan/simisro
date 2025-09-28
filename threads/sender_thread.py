from PyQt5.QtCore import QThread, pyqtSignal
import socket
import time

class SenderThread(QThread):
    packet_sent = pyqtSignal(int, float)
    record_sent = pyqtSignal(int, float)
    bytes_sent_signal = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, group="127.0.0.1", port=12345, ttl=1):
        super().__init__()
        self.group = group
        self.port = port
        self.ttl = ttl
        self.sock = None
        self.total_bytes = 0
        self._queue = []
        self.paused = False

    def configure_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.ttl)

    def enqueue(self, record_idx, record_time, packets):
        self._queue.append((record_idx, packets))

    def run(self):
        self.running = True
        self.configure_socket()
        while self.running:
            if self.paused:
                self.msleep(50)
                continue
            if not self._queue:
                self.msleep(1)  # Minimal sleep time
                continue
            
            # Process all available records in the queue
            while self._queue and self.running and not self.paused:
                record_idx, packets = self._queue.pop(0)
                bytes_sent = 0
                for i, pkt in enumerate(packets):
                    try:
                        self.sock.sendto(pkt, (self.group, int(self.port)))
                        bytes_sent += len(pkt)
                        self.packet_sent.emit(i, time.time())
                    except Exception as e:
                        self.error.emit(str(e))
                self.total_bytes += bytes_sent
                self.bytes_sent_signal.emit(self.total_bytes)
                self.record_sent.emit(record_idx, time.time())

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def stop(self):
        self.running = False
        self.quit()
        self.wait()