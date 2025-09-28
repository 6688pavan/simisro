#!/usr/bin/env python3
"""
Advanced Telemetry Listener with Parameter Parsing
This version can parse actual parameter definitions and display meaningful data.
"""

import socket
import struct
import time
import threading
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QTextEdit, QPushButton, QLineEdit, 
                             QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
                             QTabWidget, QTreeWidget, QTreeWidgetItem, QSplitter)
from PyQt5.QtCore import QTimer, pyqtSignal, QObject, QThread
from PyQt5.QtGui import QFont

class ParameterDefinition:
    """Represents a parameter definition"""
    def __init__(self, name, packet_id, offset, dtype, min_v, max_v, 
                 waveform, freq, phase, samples_per_500ms, enabled, bit_width):
        self.name = name
        self.packet_id = packet_id
        self.offset = offset
        self.dtype = dtype
        self.min_v = min_v
        self.max_v = max_v
        self.waveform = waveform
        self.freq = freq
        self.phase = phase
        self.samples_per_500ms = samples_per_500ms
        self.enabled = enabled
        self.bit_width = bit_width

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

class AdvancedPacketParser:
    """Advanced parser that can handle parameter definitions and extract values"""
    
    def __init__(self, packet_length=1400, packets_per_record=10, time_field_offset=24):
        self.packet_length = packet_length
        self.packets_per_record = packets_per_record
        self.time_field_offset = time_field_offset
        self.parameters = []  # Will be loaded from file or manual definition
        
    def load_parameters_from_file(self, filepath):
        """Load parameter definitions from a .dat file"""
        try:
            with open(filepath, "rb") as f:
                # Read parameter count
                param_count_bytes = f.read(4)
                if len(param_count_bytes) < 4:
                    return False
                
                param_count = struct.unpack('<I', param_count_bytes)[0]
                
                # Read parameters
                parameters = []
                for _ in range(param_count):
                    # Read parameter name
                    name_len_bytes = f.read(4)
                    if len(name_len_bytes) < 4:
                        break
                    name_len = struct.unpack('<I', name_len_bytes)[0]
                    name_bytes = f.read(name_len)
                    name = name_bytes.decode('utf-8')
                    
                    # Read parameter data
                    packet_id = struct.unpack('<I', f.read(4))[0]
                    offset = struct.unpack('<I', f.read(4))[0]
                    type_flag = struct.unpack('<I', f.read(4))[0]
                    dtype = "float" if type_flag == 1 else "bit"
                    min_v = struct.unpack('<f', f.read(4))[0]
                    max_v = struct.unpack('<f', f.read(4))[0]
                    freq = struct.unpack('<f', f.read(4))[0]
                    phase = struct.unpack('<f', f.read(4))[0]
                    samples_per_500ms = struct.unpack('<I', f.read(4))[0]
                    enabled_flag = struct.unpack('<I', f.read(4))[0]
                    enabled = enabled_flag == 1
                    bit_width = struct.unpack('<I', f.read(4))[0]
                    
                    param = ParameterDefinition(
                        name=name, packet_id=packet_id, offset=offset, dtype=dtype,
                        min_v=min_v, max_v=max_v, waveform="Sine", freq=freq, phase=phase,
                        samples_per_500ms=samples_per_500ms, enabled=enabled, bit_width=bit_width
                    )
                    parameters.append(param)
                
                # Read separator
                separator = f.read(10)
                if separator == b'END_PARAMS':
                    self.parameters = parameters
                    return True
                    
        except Exception as e:
            print(f"Error loading parameters: {e}")
            return False
        
        return False
    
    def add_manual_parameter(self, name, packet_id, offset, dtype="float", bit_width=8):
        """Add a parameter definition manually"""
        param = ParameterDefinition(
            name=name, packet_id=packet_id, offset=offset, dtype=dtype,
            min_v=0.0, max_v=100.0, waveform="Sine", freq=1.0, phase=0.0,
            samples_per_500ms=1, enabled=True, bit_width=bit_width
        )
        self.parameters.append(param)
    
    def parse_record(self, packets):
        """Parse a complete record using parameter definitions"""
        if len(packets) != self.packets_per_record:
            return None
            
        record_data = {
            'record_time': None,
            'parameters': {}
        }
        
        # Extract time from first packet
        if len(packets[0]) > self.time_field_offset + 4:
            time_bytes = packets[0][self.time_field_offset:self.time_field_offset+4]
            record_data['record_time'] = struct.unpack('<f', time_bytes)[0]
        
        # Parse each parameter
        for param in self.parameters:
            if not param.enabled:
                continue
                
            packet_id = param.packet_id
            if packet_id >= len(packets):
                continue
                
            packet = packets[packet_id]
            values = []
            
            if param.samples_per_500ms == 1:  # Major cycle - single value
                if param.dtype == "float":
                    if param.offset + 4 <= len(packet):
                        value_bytes = packet[param.offset:param.offset+4]
                        value = struct.unpack('<f', value_bytes)[0]
                        values.append(value)
                else:  # Digital
                    if param.offset < len(packet):
                        if param.bit_width == 8:
                            value = packet[param.offset]
                        elif param.bit_width == 16:
                            if param.offset + 2 <= len(packet):
                                value_bytes = packet[param.offset:param.offset+2]
                                value = struct.unpack('<H', value_bytes)[0]
                            else:
                                continue
                        elif param.bit_width == 32:
                            if param.offset + 4 <= len(packet):
                                value_bytes = packet[param.offset:param.offset+4]
                                value = struct.unpack('<I', value_bytes)[0]
                            else:
                                continue
                        else:
                            continue
                        values.append(value)
            else:  # Minor cycle - 5 samples
                for i in range(5):
                    if param.dtype == "float":
                        offset = param.offset + (i * 4)
                        if offset + 4 <= len(packet):
                            value_bytes = packet[offset:offset+4]
                            value = struct.unpack('<f', value_bytes)[0]
                            values.append(value)
                    else:  # Digital
                        offset = param.offset + (i * 8)
                        if offset < len(packet):
                            value = packet[offset] & 0xFF
                            values.append(value)
            
            if values:
                record_data['parameters'][param.name] = {
                    'values': values,
                    'packet_id': packet_id,
                    'offset': param.offset,
                    'dtype': param.dtype,
                    'samples_per_500ms': param.samples_per_500ms,
                    'bit_width': param.bit_width
                }
        
        return record_data

class AdvancedTelemetryDisplay(QMainWindow):
    """Advanced telemetry display with parameter parsing"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced Telemetry Listener")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize components
        self.listener = TelemetryListener()
        self.parser = AdvancedPacketParser()
        self.packet_count = 0
        self.record_count = 0
        self.packets_buffer = []
        
        self.setup_ui()
        self.connect_signals()
        
        # Load default parameters if available
        self.load_default_parameters()
        
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
        self.load_params_btn = QPushButton("Load Parameters")
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(self.clear_btn)
        control_layout.addWidget(self.load_params_btn)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # Statistics panel
        stats_group = QGroupBox("Statistics")
        stats_layout = QHBoxLayout()
        
        self.packets_label = QLabel("Packets Received: 0")
        self.records_label = QLabel("Records Parsed: 0")
        self.last_time_label = QLabel("Last Packet: None")
        self.params_label = QLabel("Parameters Loaded: 0")
        
        stats_layout.addWidget(self.packets_label)
        stats_layout.addWidget(self.records_label)
        stats_layout.addWidget(self.last_time_label)
        stats_layout.addWidget(self.params_label)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Main content area with tabs
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Parameter values tab
        self.setup_parameters_tab()
        
        # Raw data tab
        self.setup_raw_data_tab()
        
        # Log tab
        self.setup_log_tab()
        
    def setup_parameters_tab(self):
        """Setup the parameters display tab"""
        params_widget = QWidget()
        params_layout = QVBoxLayout(params_widget)
        
        # Parameters table
        self.params_table = QTableWidget()
        self.params_table.setColumnCount(5)
        self.params_table.setHorizontalHeaderLabels(["Parameter", "Value(s)", "Packet", "Offset", "Time"])
        
        # Set column widths
        header = self.params_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        params_layout.addWidget(self.params_table)
        self.tab_widget.addTab(params_widget, "Parameter Values")
        
    def setup_raw_data_tab(self):
        """Setup the raw data display tab"""
        raw_widget = QWidget()
        raw_layout = QVBoxLayout(raw_widget)
        
        # Raw data table
        self.raw_table = QTableWidget()
        self.raw_table.setColumnCount(4)
        self.raw_table.setHorizontalHeaderLabels(["Packet ID", "Offset", "Value", "Time"])
        
        # Set column widths
        header = self.raw_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        raw_layout.addWidget(self.raw_table)
        self.tab_widget.addTab(raw_widget, "Raw Data")
        
    def setup_log_tab(self):
        """Setup the log display tab"""
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        
        log_layout.addWidget(self.log_text)
        self.tab_widget.addTab(log_widget, "Log")
        
    def connect_signals(self):
        """Connect UI signals"""
        self.start_btn.clicked.connect(self.start_listening)
        self.stop_btn.clicked.connect(self.stop_listening)
        self.clear_btn.clicked.connect(self.clear_display)
        self.load_params_btn.clicked.connect(self.load_parameters)
        
        self.listener.packet_received.connect(self.on_packet_received)
        self.listener.error_occurred.connect(self.on_error)
        
    def load_default_parameters(self):
        """Load default parameters from test_data.dat if available"""
        if self.parser.load_parameters_from_file("test_data.dat"):
            self.log_message(f"Loaded {len(self.parser.parameters)} parameters from test_data.dat")
            self.update_params_label()
        else:
            # Add some manual parameters for testing
            self.parser.add_manual_parameter("temperature", 0, 4, "float")
            self.parser.add_manual_parameter("pressure", 0, 8, "float")
            self.parser.add_manual_parameter("voltage", 1, 0, "float")
            self.log_message("Using default manual parameters")
            self.update_params_label()
    
    def load_parameters(self):
        """Load parameters from file"""
        from PyQt5.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getOpenFileName(self, "Load Parameters", "", "DAT Files (*.dat)")
        if filename:
            if self.parser.load_parameters_from_file(filename):
                self.log_message(f"Loaded {len(self.parser.parameters)} parameters from {filename}")
                self.update_params_label()
            else:
                self.log_message(f"Failed to load parameters from {filename}", "ERROR")
    
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
        self.stop_btn.setEnabled(True)
    
    def clear_display(self):
        """Clear the data display"""
        self.params_table.setRowCount(0)
        self.raw_table.setRowCount(0)
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
        """Display parsed record data"""
        current_time = time.strftime("%H:%M:%S", time.localtime(timestamp))
        
        # Display parameter values
        self.display_parameter_values(record_data, current_time)
        
        # Display raw data
        self.display_raw_data(record_data, current_time)
    
    def display_parameter_values(self, record_data, current_time):
        """Display parameter values in the parameters table"""
        for param_name, param_data in record_data['parameters'].items():
            values = param_data['values']
            
            # Format values display
            if len(values) == 1:
                values_text = f"{values[0]:.6f}"
            else:
                values_text = " | ".join([f"{v:.6f}" for v in values])
            
            # Add new row
            row = self.params_table.rowCount()
            self.params_table.insertRow(row)
            
            # Set values
            self.params_table.setItem(row, 0, QTableWidgetItem(param_name))
            self.params_table.setItem(row, 1, QTableWidgetItem(values_text))
            self.params_table.setItem(row, 2, QTableWidgetItem(str(param_data['packet_id'])))
            self.params_table.setItem(row, 3, QTableWidgetItem(str(param_data['offset'])))
            self.params_table.setItem(row, 4, QTableWidgetItem(current_time))
        
        # Scroll to bottom
        self.params_table.scrollToBottom()
        
        # Limit table size
        if self.params_table.rowCount() > 500:
            self.params_table.removeRow(0)
    
    def display_raw_data(self, record_data, current_time):
        """Display raw data in the raw data table"""
        # This would show all float values from all packets
        # For now, just show a summary
        pass
    
    def update_statistics(self):
        """Update statistics display"""
        self.packets_label.setText(f"Packets Received: {self.packet_count}")
        self.records_label.setText(f"Records Parsed: {self.record_count}")
        
        if self.packet_count > 0:
            current_time = time.strftime("%H:%M:%S", time.localtime())
            self.last_time_label.setText(f"Last Packet: {current_time}")
    
    def update_params_label(self):
        """Update parameters count label"""
        self.params_label.setText(f"Parameters Loaded: {len(self.parser.parameters)}")
    
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
    window = AdvancedTelemetryDisplay()
    window.show()
    
    # Run application
    app.exec_()

if __name__ == "__main__":
    main()
