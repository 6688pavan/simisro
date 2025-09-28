#!/usr/bin/env python3
"""
Test script to verify digital parameter functionality.
"""

import sys
import time
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, QObject, pyqtSignal
from gui.main_window import MainWindow
from core.models import Parameter

class DigitalParamTester(QObject):
    """Test class to monitor digital parameter generation"""
    
    def __init__(self):
        super().__init__()
        self.records_sent = 0
        self.start_time = None
        self.test_duration = 10  # 10 seconds
        self.expected_records = 20  # 2 Hz * 10 seconds = 20 records
        
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
        
        print(f"\n=== DIGITAL PARAMETER TEST RESULTS ===")
        print(f"Test Duration: {actual_duration:.2f} seconds")
        print(f"Records Sent: {self.records_sent}")
        print(f"Expected Records: {self.expected_records}")
        print(f"Actual Rate: {records_per_second:.2f} records/second")
        print(f"Expected Rate: 2.0 records/second")
        
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

def run_digital_param_test():
    """Run the digital parameter test"""
    print("Starting Digital Parameter Test...")
    print("Testing digital parameters with different bit widths")
    print("-" * 50)
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Create main window
    main_window = MainWindow()
    
    # Create tester
    tester = DigitalParamTester()
    
    # Create test parameters with different bit widths
    test_params = [
        Parameter(
            name="analog_param",
            packet_id=0,
            offset=4,
            dtype="float",
            min_v=0.0,
            max_v=100.0,
            waveform="Sine",
            freq=0.1,
            phase=0.0,
            samples_per_500ms=1,
            enabled=True,
            bit_width=8  # Not used for float
        ),
        Parameter(
            name="digital_8bit",
            packet_id=0,
            offset=8,
            dtype="bit",
            min_v=0.0,
            max_v=255.0,
            waveform="Square",
            freq=0.5,
            phase=0.0,
            samples_per_500ms=1,
            enabled=True,
            bit_width=8
        ),
        Parameter(
            name="digital_16bit",
            packet_id=0,
            offset=12,
            dtype="bit",
            min_v=0.0,
            max_v=65535.0,
            waveform="Triangle",
            freq=0.2,
            phase=0.0,
            samples_per_500ms=1,
            enabled=True,
            bit_width=16
        ),
        Parameter(
            name="digital_32bit",
            packet_id=0,
            offset=16,
            dtype="bit",
            min_v=0.0,
            max_v=4294967295.0,
            waveform="Step",
            freq=0.1,
            phase=0.0,
            samples_per_500ms=1,
            enabled=True,
            bit_width=32
        ),
        Parameter(
            name="digital_minor_cycle",
            packet_id=0,
            offset=20,
            dtype="bit",
            min_v=0.0,
            max_v=255.0,
            waveform="Noise",
            freq=1.0,
            phase=0.0,
            samples_per_500ms=5,
            enabled=True,
            bit_width=8
        )
    ]
    
    # Load parameters
    main_window.parameters = test_params
    main_window.param_table.load_parameters(test_params)
    print(f"Created {len(test_params)} test parameters:")
    for param in test_params:
        print(f"  - {param.name} ({param.dtype}, {param.bit_width}bit, {param.samples_per_500ms} samples)")
    
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
    
    # Set up timer to stop test after 10 seconds
    timer = QTimer()
    timer.timeout.connect(lambda: tester.on_test_complete(main_window))
    timer.setSingleShot(True)
    timer.start(10000)  # 10 seconds
    
    # Run the application
    app.exec_()

if __name__ == "__main__":
    run_digital_param_test()
