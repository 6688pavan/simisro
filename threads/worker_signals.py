from PyQt5.QtCore import pyqtSignal, QObject

class WorkerSignals(QObject):
    record_ready = pyqtSignal(int, float, list)  # record_index, record_time, packets (list of bytes)
    packet_sent = pyqtSignal(int, float)  # packet_id, send_time
    record_sent = pyqtSignal(int)  # record_idx
    sample_generated = pyqtSignal(str, float, float)  # param_name, sample_time, value
    error = pyqtSignal(str)
    log_message = pyqtSignal(str, str)  # message, level (INFO/WARNING/ERROR)