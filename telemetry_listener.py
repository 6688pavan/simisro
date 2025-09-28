#!/usr/bin/env python3
"""
Telemetry Listener - A separate program to listen to multicast telemetry data
and display the received parameter values in real-time.
"""

import socket
import struct
import time
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QTextEdit, QPushButton, QLineEdit, 
                             QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import QTimer, pyqtSignal, QObject, QThread
from PyQt5.QtGui import QFont

class TelemetryListener(QObject):
    """UDP multicast listener that receives telemetry packets"""
    
    packet_received = pyqtSignal(bytes, float)  # packet_data, timestamp
    error_occurred = pyqtSignal(str)
    
    def __init__(self, group="239.0.0.1", port=12345):
        super().__init__()
        self.group = group
        self.port = port
        self.sock = None
        self.running = False
        self.listen_thread = None
        
    def start_listening(self):
        """Start listening for multicast packets"""
        try:
            # Create UDP socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to multicast group
            self.sock.bind(('', self.port))
            
            # Join multicast group
            mreq = struct.pack("4sl", socket.inet_aton(self.group), socket.INADDR_ANY)
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            
            self.running = True
            self.listen_thread = threading.Thread(target=self._listen_loop)
            self.listen_thread.daemon = True
            self.listen_thread.start()
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to start listening: {str(e)}")
    
    def stop_listening(self):
        """Stop listening for packets"""
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        if self.listen_thread:
            self.listen_thread.join(timeout=1.0)
    
    def _listen_loop(self):
        """Main listening loop"""
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1400)  # Max packet size
                timestamp = time.time()
                self.packet_received.emit(data, timestamp)
            except Exception as e:
                if self.running:  # Only emit error if we're still supposed to be running
                    self.error_occurred.emit(f"Error receiving packet: {str(e)}")
                break

class PacketParser:
    """Parses telemetry packets to extract parameter values"""
    
    def __init__(self, packet_length=1400, packets_per_record=10, time_field_offset=24):
        self.packet_length = packet_length
        self.packets_per_record = packets_per_record
        self.time_field_offset = time_field_offset
        
    def parse_record(self, packets):
        """Parse a complete record (10 packets) and extract parameter values"""
        if len(packets) != self.packets_per_record:
            return None
            
        record_data = {}
        
        # Extract time from first packet
        if len(packets[0]) > self.time_field_offset + 4:
            time_bytes = packets[0][self.time_field_offset:self.time_field_offset+4]
            record_time = struct.unpack('<f', time_bytes)[0]
            record_data['record_time'] = record_time
        
        # Parse each packet for float values
        for packet_id, packet in enumerate(packets):
            packet_data = {}
            
            # Extract float values every 4 bytes (assuming float parameters)
            for offset in range(0, min(len(packet), self.packet_length), 4):
                if offset + 4 <= len(packet):
                    try:
                        value_bytes = packet[offset:offset+4]
                        float_value = struct.unpack('<f', value_bytes)[0]
                        packet_data[f'offset_{offset}'] = float_value
                    except:
                        pass
            
            record_data[f'packet_{packet_id}'] = packet_data
        
        return record_data

class TelemetryDisplay(QMainWindow):
    """Main window for displaying received telemetry data"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Telemetry Listener")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize components
        self.listener = TelemetryListener()
        self.parser = PacketParser()
        self.packet_count = 0
        self.record_count = 0
        self.packets_buffer = []
        
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Control panel
        control_group = QGroupBox("Listener Controls")
        control_layout = QHBoxLayout()
        
        # Network settings
        control_layout.addWidget(QLabel("Multicast IP:"))
        self.ip_edit = QLineEdit("239.0.0.1")
        self.ip_edit.setMaximumWidth(120)
        control_layout.addWidget(self.ip_edit)
        
        control_layout.addWidget(QLabel("Port:"))
        self.port_edit = QLineEdit("12345")
        self.port_edit.setMaximumWidth(80)
        control_layout.addWidget(self.port_edit)
        
        # Control buttons
        self.start_btn = QPushButton("Start Listening")
        self.stop_btn = QPushButton("Stop Listening")
        self.clear_btn = QPushButton("Clear Display")
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(self.clear_btn)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # Statistics panel
        stats_group = QGroupBox("Statistics")
        stats_layout = QHBoxLayout()
        
        self.packets_label = QLabel("Packets Received: 0")
        self.records_label = QLabel("Records Parsed: 0")
        self.last_time_label = QLabel("Last Packet: None")
        
        stats_layout.addWidget(self.packets_label)
        stats_layout.addWidget(self.records_label)
        stats_layout.addWidget(self.last_time_label)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Data display table
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(4)
        self.data_table.setHorizontalHeaderLabels(["Packet ID", "Offset", "Value", "Time"])
        
        # Set column widths
        header = self.data_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.data_table)
        
        # Log display
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
    def connect_signals(self):
        """Connect UI signals"""
        self.start_btn.clicked.connect(self.start_listening)
        self.stop_btn.clicked.connect(self.stop_listening)
        self.clear_btn.clicked.connect(self.clear_display)
        
        self.listener.packet_received.connect(self.on_packet_received)
        self.listener.error_occurred.connect(self.on_error)
        
    def start_listening(self):
        """Start listening for multicast packets"""
        try:
            group = self.ip_edit.text()
            port = int(self.port_edit.text())
            
            self.listener.group = group
            self.listener.port = port
            
            self.listener.start_listening()
            self.log_message(f"Started listening on {group}:{port}")
            
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            
        except Exception as e:
            self.log_message(f"Error starting listener: {str(e)}", "ERROR")
    
    def stop_listening(self):
        """Stop listening for packets"""
        self.listener.stop_listening()
        self.log_message("Stopped listening")
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
    
    def clear_display(self):
        """Clear the data display"""
        self.data_table.setRowCount(0)
        self.packet_count = 0
        self.record_count = 0
        self.packets_buffer = []
        self.update_statistics()
        self.log_message("Display cleared")
    
    def on_packet_received(self, packet_data, timestamp):
        """Handle received packet"""
        self.packet_count += 1
        self.packets_buffer.append(packet_data)
        
        # When we have 10 packets, parse as a complete record
        if len(self.packets_buffer) >= 10:
            record_data = self.parser.parse_record(self.packets_buffer[:10])
            if record_data:
                self.display_record(record_data, timestamp)
                self.record_count += 1
            
            # Keep only the last 9 packets for next record
            self.packets_buffer = self.packets_buffer[-9:]
        
        self.update_statistics()
    
    def display_record(self, record_data, timestamp):
        """Display parsed record data in the table"""
        current_time = time.strftime("%H:%M:%S", time.localtime(timestamp))
        
        # Add rows for each packet's data
        for packet_key, packet_data in record_data.items():
            if packet_key.startswith('packet_'):
                packet_id = packet_key.split('_')[1]
                
                for offset_key, value in packet_data.items():
                    if offset_key.startswith('offset_'):
                        offset = offset_key.split('_')[1]
                        
                        # Add new row
                        row = self.data_table.rowCount()
                        self.data_table.insertRow(row)
                        
                        # Set values
                        self.data_table.setItem(row, 0, QTableWidgetItem(packet_id))
                        self.data_table.setItem(row, 1, QTableWidgetItem(offset))
                        self.data_table.setItem(row, 2, QTableWidgetItem(f"{value:.6f}"))
                        self.data_table.setItem(row, 3, QTableWidgetItem(current_time))
        
        # Scroll to bottom
        self.data_table.scrollToBottom()
        
        # Limit table size (keep last 1000 rows)
        if self.data_table.rowCount() > 1000:
            self.data_table.removeRow(0)
    
    def update_statistics(self):
        """Update statistics display"""
        self.packets_label.setText(f"Packets Received: {self.packet_count}")
        self.records_label.setText(f"Records Parsed: {self.record_count}")
        
        if self.packet_count > 0:
            current_time = time.strftime("%H:%M:%S", time.localtime())
            self.last_time_label.setText(f"Last Packet: {current_time}")
    
    def on_error(self, error_message):
        """Handle errors"""
        self.log_message(error_message, "ERROR")
    
    def log_message(self, message, level="INFO"):
        """Add message to log"""
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        color = {"INFO": "black", "ERROR": "red", "WARNING": "orange"}.get(level, "black")
        
        formatted_message = f'<font color="{color}">[{timestamp}] {level}: {message}</font>'
        self.log_text.append(formatted_message)
        self.log_text.ensureCursorVisible()
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.stop_listening()
        event.accept()

def main():
    """Main function"""
    app = QApplication([])
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = TelemetryDisplay()
    window.show()
    
    # Run application
    app.exec_()

if __name__ == "__main__":
    main()
