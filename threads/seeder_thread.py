from PyQt5.QtCore import QThread, QTimer, QMetaObject, Qt
from .worker_signals import WorkerSignals

class SeederThread(QThread):
    def __init__(self, seeding_engine, start_time=-900.0, end_time=1200.0, hz=2.0):
        super().__init__()
        self.seeding_engine = seeding_engine
        self.start_time = start_time
        self.end_time = end_time
        self.hz = hz
        self.interval = int(1000 / hz)  # ms
        self.current_time = start_time
        self.record_index = 0
        self.running = False
        self.paused = False
        self.signals = WorkerSignals()

    def run(self):
        self.running = True
        self.current_time = self.start_time
        self.record_index = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.generate_record)
        self.timer.start(self.interval)
        self.exec_()

    def generate_record(self):
        if not self.running or self.paused:
            return
        if self.current_time > self.end_time:
            self.stop()
            return
        try:
            buffer = self.seeding_engine.seed_record(self.current_time)
            packets = buffer.get_packets()
            self.signals.record_ready.emit(self.record_index, self.current_time, packets)
            self.signals.log_message.emit(f"Generated record {self.record_index} at time {self.current_time}", "INFO")
            self.current_time += 1 / self.hz
            self.record_index += 1
        except Exception as e:
            self.signals.error.emit(str(e))
            self.signals.log_message.emit(str(e), "ERROR")

    def pause(self):
        self.paused = True
        self.signals.log_message.emit("Simulation paused", "INFO")

    def resume(self):
        self.paused = False
        self.signals.log_message.emit("Simulation resumed", "INFO")

    def stop(self):
        self.running = False
        # Stop the timer and quit the event loop from the thread that owns them
        if hasattr(self, 'timer'):
            # Use a queued invoke so the stop() call runs in the timer's thread
            QMetaObject.invokeMethod(self.timer, "stop", Qt.QueuedConnection)
            # Also schedule deletion of the timer in its thread
            QMetaObject.invokeMethod(self.timer, "deleteLater", Qt.QueuedConnection)
        # Request the event loop to quit from the thread's context
        QMetaObject.invokeMethod(self, "quit", Qt.QueuedConnection)
        # Wait for the thread to finish
        self.wait()
        self.signals.log_message.emit("Simulation stopped", "INFO")