#!/usr/bin/env python3
"""
Test script to verify simulation timing at 2 Hz for 30 seconds.
Should send exactly 60 records in 30 seconds.
"""

import sys
import time
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, QObject, pyqtSignal
from gui.main_window import MainWindow
from core.loader import Loader

class SimulationTester(QObject):
    """Test class to monitor simulation progress"""
    
    def __init__(self):
        super().__init__()
        self.records_sent = 0
        self.start_time = None
        self.end_time = None
        self.test_duration = 30  # 30 seconds
        self.expected_records = 60  # 2 Hz * 30 seconds = 60 records
        
    def on_record_sent(self, record_idx, timestamp):
        """Called when a record is sent"""
        self.records_sent = record_idx + 1
        if self.start_time is None:
            self.start_time = time.time()
            print(f"Test started at {self.start_time:.2f}")
        print(f"Record {self.records_sent} sent at {time.time():.2f}")
        
    def on_test_complete(self, main_window):
        """Called when test duration is complete"""
        self.end_time = time.time()
        actual_duration = self.end_time - self.start_time
        records_per_second = self.records_sent / actual_duration
        
        print(f"\n=== TEST RESULTS ===")
        print(f"Test Duration: {actual_duration:.2f} seconds")
        print(f"Records Sent: {self.records_sent}")
        print(f"Expected Records: {self.expected_records}")
        print(f"Actual Rate: {records_per_second:.2f} records/second")
        print(f"Expected Rate: 2.0 records/second")
        print(f"Timer triggered at: {self.end_time:.2f}")
        
        # Check if simulation is still running
        if main_window.seeder_thread and main_window.seeder_thread.running:
            print("Simulation was still running when timer triggered")
        else:
            print("Simulation had already stopped")
        
        # Verify results
        if self.records_sent == self.expected_records:
            print("✅ PASS: Correct number of records sent")
        else:
            print(f"❌ FAIL: Expected {self.expected_records}, got {self.records_sent}")
            
        if abs(records_per_second - 2.0) < 0.1:
            print("✅ PASS: Correct transmission rate")
        else:
            print(f"❌ FAIL: Expected 2.0 Hz, got {records_per_second:.2f} Hz")
            
        # Stop the application
        QApplication.quit()

def run_timing_test():
    """Run the simulation timing test"""
    print("Starting Simulation Timing Test...")
    print("Testing 2 Hz transmission for 30 seconds")
    print("Expected: 60 records in 30 seconds")
    print("-" * 50)
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Create main window
    main_window = MainWindow()
    
    # Create tester
    tester = SimulationTester()
    
    # Load test data if available
    try:
        loader = Loader()
        result = loader.load_dat("test_data.dat")
        if isinstance(result, tuple):
            main_window.dat_buffer, parameters = result
            if parameters:
                main_window.parameters = parameters
                main_window.param_table.load_parameters(parameters)
                print(f"Loaded test data with {len(parameters)} parameters")
            else:
                print("No parameters found in test data")
        else:
            print("Loaded old format test data")
    except Exception as e:
        print(f"Could not load test data: {e}")
        print("Creating test parameters manually...")
        
        # Create a simple test parameter
        from core.models import Parameter
        test_param = Parameter(
            name="test_timing",
            packet_id=0,
            offset=4,
            dtype="float",
            min_v=0.0,
            max_v=100.0,
            waveform="Sine",
            freq=0.1,
            phase=0.0,
            samples_per_500ms=1,
            enabled=True
        )
        main_window.parameters = [test_param]
        main_window.param_table.load_parameters([test_param])
    
    # Set test parameters
    main_window.start_time_edit.setText("0.0")
    main_window.end_time_edit.setText("1200.0")
    main_window.hz_combo.setCurrentText("2")
    
    # Show window
    main_window.show()
    
    # Start simulation
    print("Starting simulation...")
    main_window.on_start()
    
    # Connect signals after starting simulation
    if main_window.sender_thread:
        main_window.sender_thread.record_sent.connect(tester.on_record_sent)
    
    # Set up timer to stop test after 30 seconds
    timer = QTimer()
    timer.timeout.connect(lambda: tester.on_test_complete(main_window))
    timer.setSingleShot(True)
    timer.start(30000)  # 30 seconds
    
    # Run the application
    app.exec_()

if __name__ == "__main__":
    run_timing_test()
