from PyQt5.QtCore import QThread
from .worker_signals import WorkerSignals
import time

class SenderThread(QThread):
    def __init__(self, multicast_sender):
        super().__init__()
        self.multicast_sender = multicast_sender
        self.running = True
        self.signals = WorkerSignals()

    def run(self):
        self.exec_()

    def on_record_ready(self, record_index, record_time, packets):
        if not self.running:
            return
        try:
            start_send = time.time()
            self.multicast_sender.send_packets(packets)
            for packet_id in range(len(packets)):
                self.signals.packet_sent.emit(packet_id, time.time())
            self.signals.record_sent.emit(record_index)
            self.signals.log_message.emit(f"Sent record {record_index} ({len(packets)} packets)", "INFO")
        except Exception as e:
            self.signals.error.emit(str(e))
            self.signals.log_message.emit(str(e), "ERROR")

    def stop(self):
        self.running = False
        self.quit()
        self.wait()