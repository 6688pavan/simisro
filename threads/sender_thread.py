from PyQt5.QtCore import QThread, pyqtSignal
import socket
import time
import threading
from queue import Queue

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
        self.queue = Queue(maxsize=100)
        # Use Event for pause/resume semantics (set = running, clear = paused)
        self.pause_event = threading.Event()
        self.pause_event.set()

    def configure_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.ttl)

    def enqueue(self, record_idx, record_time, packets):
        try:
            self.queue.put((record_idx, packets), block=True)
        except Exception as e:
            self.error.emit(str(e))

    def run(self):
        self.running = True
        self.configure_socket()
        while self.running:
            try:
                item = self.queue.get(timeout=0.1)
            except Exception:
                continue
            if item is None:
                break
            # Ensure we respect pause
            self.pause_event.wait()
            record_idx, packets = item
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
            self.queue.task_done()

    def pause(self):
        self.pause_event.clear()

    def resume(self):
        self.pause_event.set()

    def stop(self):
        self.running = False
        # Ensure we can exit even if paused
        self.pause_event.set()
        try:
            self.queue.put(None, block=False)
        except Exception:
            pass
        self.quit()
        self.wait()