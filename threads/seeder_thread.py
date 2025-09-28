from PyQt5.QtCore import QThread, pyqtSignal
import time

class SeederThread(QThread):
    record_ready = pyqtSignal(int, float, list)  # record_idx, record_time, packets
    error = pyqtSignal(str)
    
    def __init__(self, params_getter, seeding_engine, dat_buffer=None, start_time=-900.0, end_time=1200.0, hz=2.0):
        super().__init__()
        self.params_getter = params_getter
        self.seeding_engine = seeding_engine
        self.dat_buffer = dat_buffer
        self.start_time = start_time
        self.end_time = end_time
        self.hz = hz
        self.running = False
        self.paused = False

    def run(self):
        self.running = True
        current_time = self.start_time
        record_idx = 0
        time_increment = 1.0 / self.hz  # Time increment per record based on Hz
        
        while self.running and current_time <= self.end_time:
            if self.paused:
                time.sleep(0.05)
                continue
            try:
                buffer = self.seeding_engine.seed_record(self.params_getter(), current_time, self.dat_buffer, time_increment)
                packets = buffer.get_packets()
                self.record_ready.emit(record_idx, current_time, packets)
                record_idx += 1
                
                # Sleep for the transmission interval
                sleep_time = time_increment
                time.sleep(sleep_time)
                
                # Advance time by the increment (1 second for 1Hz, 0.2 seconds for 5Hz, etc.)
                current_time += time_increment
                
            except Exception as e:
                self.error.emit(str(e))

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def stop(self):
        self.running = False
        self.quit()
        self.wait()