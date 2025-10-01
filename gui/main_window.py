from PyQt5.QtWidgets import (QMainWindow, QSplitter, QHBoxLayout, QVBoxLayout, QWidget, 
                             QGroupBox, QPushButton, QLineEdit, QLabel, QFileDialog, 
                             QSpinBox, QComboBox, QGridLayout, QTextEdit)
from PyQt5.QtCore import Qt
from gui.widgets.param_table import ParameterTableWidget
from gui.widgets.waveform_plot import WaveformPlotWidget
from gui.parameter_editor import ParameterEditorDialog
from threads.seeder_thread import SeederThread
from threads.sender_thread import SenderThread
from core.seeder import SeedingEngine
from core.loader import Loader
from utils.config import ConfigManager
from core.models import Parameter

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Telemetry Simulator")
        self.parameters = []
        self.dat_buffer = None
        self.seeder_thread = None
        self.sender_thread = None
        self.seeding_engine = SeedingEngine()
        self.loader = Loader()
        self.config_manager = ConfigManager()
        self.setup_ui()
        self.connect_signals()
        self.apply_grey_theme()

    def setup_ui(self):
        central = QWidget()
        main_lay = QVBoxLayout()
        central.setLayout(main_lay)
        self.setCentralWidget(central)

        # Top Bar: Buttons
        top_bar = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.pause_btn = QPushButton("Pause")
        self.resume_btn = QPushButton("Resume")
        self.stop_btn = QPushButton("Reset")
        self.export_btn = QPushButton("Export Config")
        self.load_btn = QPushButton("Load Config")
        self.browse_btn = QPushButton("Browse File")
        
        top_bar.addWidget(self.start_btn)
        top_bar.addWidget(self.pause_btn)
        top_bar.addWidget(self.resume_btn)
        top_bar.addWidget(self.stop_btn)
        top_bar.addWidget(self.export_btn)
        top_bar.addWidget(self.load_btn)
        top_bar.addWidget(self.browse_btn)
        main_lay.addLayout(top_bar)

        # Top Panes (QGridLayout)
        top_panes = QGridLayout()
        
        # Left: Start/End Time, Transmission Hz
        time_group = QGroupBox("Time & Hz")
        time_lay = QVBoxLayout()
        time_lay.addWidget(QLabel("Start Time:"))
        self.start_time_edit = QLineEdit("-900.0")
        time_lay.addWidget(self.start_time_edit)
        time_lay.addWidget(QLabel("End Time:"))
        self.end_time_edit = QLineEdit("1200.0")
        time_lay.addWidget(self.end_time_edit)
        time_lay.addWidget(QLabel("Transmission Hz:"))
        self.hz_combo = QComboBox()
        self.hz_combo.addItems(["1", "2", "5", "10", "50"])
        self.hz_combo.setCurrentText("2")
        time_lay.addWidget(self.hz_combo)
        time_group.setLayout(time_lay)
        top_panes.addWidget(time_group, 0, 0)

        # Middle: Stats
        stats_group = QGroupBox("Live Stats")
        stats_lay = QVBoxLayout()
        self.current_time_label = QLabel("Current Time: 0 sec")
        self.records_sent_label = QLabel("Records Sent: 0")
        self.bytes_sent_label = QLabel("Bytes Sent: 0")
        self.packets_per_record_label = QLabel("Packets/Record: 10")
        stats_lay.addWidget(self.current_time_label)
        stats_lay.addWidget(self.records_sent_label)
        stats_lay.addWidget(self.packets_per_record_label)
        stats_group.setLayout(stats_lay)
        top_panes.addWidget(stats_group, 0, 1)

        # Right: Multicast IP, Port
        net_group = QGroupBox("Network")
        net_lay = QVBoxLayout()
        net_lay.addWidget(QLabel("Multicast IP:"))
        self.multicast_ip_edit = QLineEdit("239.0.0.1")
        net_lay.addWidget(self.multicast_ip_edit)
        net_lay.addWidget(QLabel("Port:"))
        self.port_edit = QLineEdit("12345")
        net_lay.addWidget(self.port_edit)
        net_group.setLayout(net_lay)
        top_panes.addWidget(net_group, 0, 2)

        main_lay.addLayout(top_panes)

        # Middle (QSplitter)
        splitter = QSplitter(Qt.Horizontal)
        main_lay.addWidget(splitter)

        # Left: Parameter table with controls
        left_widget = QWidget()
        left_lay = QVBoxLayout()
        self.param_table = ParameterTableWidget(self.parameters)
        left_lay.addWidget(self.param_table)
        
        # Parameter controls
        param_controls = QHBoxLayout()
        self.add_param_btn = QPushButton("Add Parameter")
        self.edit_param_btn = QPushButton("Edit Parameter")
        self.remove_param_btn = QPushButton("Remove Parameter")
        param_controls.addWidget(self.add_param_btn)
        param_controls.addWidget(self.edit_param_btn)
        param_controls.addWidget(self.remove_param_btn)
        left_lay.addLayout(param_controls)
        
        left_widget.setLayout(left_lay)
        splitter.addWidget(left_widget)

        # Right: Waveform plot with graph options
        right_widget = QWidget()
        right_lay = QVBoxLayout()
        self.waveform_plot = WaveformPlotWidget()
        right_lay.addWidget(self.waveform_plot)
        
        # Graph options button
        self.graph_options_btn = QPushButton("Graph Options")
        right_lay.addWidget(self.graph_options_btn)
        
        right_widget.setLayout(right_lay)
        splitter.addWidget(right_widget)

        # Bottom: Log view
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        main_lay.addWidget(self.log)

    def apply_grey_theme(self):
        """Apply grey color scheme to UI elements"""
        # Set main window background
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #ffffff;
            }
            QPushButton {
                background-color: #4a4a4a;
                border: 1px solid #666666;
                border-radius: 3px;
                padding: 5px 10px;
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
                border: 1px solid #777777;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #666666;
                border: 1px solid #444444;
            }
            QLineEdit {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
                color: #ffffff;
            }
            QLineEdit:focus {
                border: 2px solid #666666;
            }
            QComboBox {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
                color: #ffffff;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                color: #ffffff;
                selection-background-color: #4a4a4a;
            }
            QLabel {
                color: #ffffff;
            }
            QTableWidget {
                background-color: #3c3c3c;
                alternate-background-color: #404040;
                border: 1px solid #555555;
                gridline-color: #555555;
                color: #ffffff;
            }
            QTableWidget::item {
                padding: 5px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #4a4a4a;
            }
            QHeaderView::section {
                background-color: #4a4a4a;
                border: 1px solid #555555;
                padding: 5px;
                color: #ffffff;
                font-weight: bold;
            }
            QTextEdit {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 3px;
                color: #ffffff;
            }
            QCheckBox {
                color: #ffffff;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid #555555;
            }
            /* Red filled when not selected */
            QCheckBox::indicator:unchecked {
                background-color: #C0392B; /* red */
            }
            /* Green filled with visible white tick when selected */
            QCheckBox::indicator:checked {
                background-color: #27AE60; /* green */
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0iI2ZmZmZmZiIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
            }
        """)

    def connect_signals(self):
        self.start_btn.clicked.connect(self.on_start)
        self.pause_btn.clicked.connect(self.on_pause)
        self.resume_btn.clicked.connect(self.on_resume)
        self.stop_btn.clicked.connect(self.on_reset)
        self.export_btn.clicked.connect(self.on_export_config)
        self.load_btn.clicked.connect(self.on_load_config)
        self.browse_btn.clicked.connect(self.on_browse_file)
        self.add_param_btn.clicked.connect(self.on_add_param)
        self.edit_param_btn.clicked.connect(self.on_edit_param)
        self.remove_param_btn.clicked.connect(self.on_remove_param)
        self.graph_options_btn.clicked.connect(self.waveform_plot._show_graph_popup)
        # Propagate Hz changes dynamically
        self.hz_combo.currentTextChanged.connect(self.on_hz_changed)

    def on_start(self):
        if not self.parameters:
            self.log.append("No parameters loaded")
            return
        # Allow simulation to start even without .dat file when parameters are manually added
        if not self.dat_buffer:
            self.log.append("No .dat file loaded - using empty buffers for simulation")
        
        ip = self.multicast_ip_edit.text()
        port = int(self.port_edit.text())
        self.sender_thread = SenderThread(group=ip, port=port)
        self.sender_thread.start()
        
        start_time = float(self.start_time_edit.text())
        end_time = float(self.end_time_edit.text())
        hz = float(self.hz_combo.currentText())
        
        self.seeder_thread = SeederThread(
            params_getter=lambda: self.parameters,
            seeding_engine=self.seeding_engine,
            dat_buffer=self.dat_buffer,
            start_time=start_time,
            end_time=end_time,
            hz=hz
        )
        self.seeder_thread.record_ready.connect(self.sender_thread.enqueue)
        self.seeder_thread.record_ready.connect(self.on_record_ready)
        self.seeder_thread.record_ready.connect(self.update_current_time)  # Update current time from seeder
        self.seeder_thread.error.connect(self.log.append)
        self.sender_thread.record_sent.connect(self.update_records_sent)
        
        # Connect seeding engine signals for real-time parameter updates
        self.seeding_engine.sample_generated.connect(self.param_table.update_instantaneous)
        # Reset live stats on start
        self.current_time_label.setText("Current Time: 0 sec")
        self.records_sent_label.setText("Records Sent: 0")
        self.seeder_thread.start()

    def on_hz_changed(self, _text: str):
        """Update running/paused seeder thread when Hz selection changes."""
        self._apply_hz_from_ui()

    def _apply_hz_from_ui(self):
        """Apply the current Hz value from the UI to the seeder thread, if present."""
        try:
            hz = float(self.hz_combo.currentText())
        except Exception:
            hz = None
        if self.seeder_thread and hz is not None:
            # SeederThread.set_hz handles validation
            self.seeder_thread.set_hz(hz)

    def on_pause(self):
        """Pause both seeder and sender threads"""
        if self.seeder_thread:
            self.seeder_thread.pause()
        if self.sender_thread:
            self.sender_thread.pause()
        self.log.append("Simulation paused")

    def on_resume(self):
        """Resume both seeder and sender threads"""
        if self.seeder_thread:
            # Ensure latest Hz is applied before resuming
            self._apply_hz_from_ui()
            self.seeder_thread.resume()
        if self.sender_thread:
            self.sender_thread.resume()
        self.log.append("Simulation resumed")

    def on_reset(self):
        """Reset the simulation to initial state"""
        if self.seeder_thread:
            self.seeder_thread.stop()
        if self.sender_thread:
            self.sender_thread.stop()
        
        # Reset all counters and displays
        self.current_time_label.setText("Current Time: 0 sec")
        self.records_sent_label.setText("Records Sent: 0")
        
        # Clear the waveform plot
        self.waveform_plot.clear_plot()
        
        # Reset parameter table instantaneous values
        for param in self.parameters:
            self.param_table.update_instantaneous(param.name, 0.0, 0.0)
        
        self.log.append("Simulation reset to initial state")

    def on_export_config(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Config", "", "JSON Files (*.json)")
        if filename:
            settings = {
                "start_time": float(self.start_time_edit.text()),
                "end_time": float(self.end_time_edit.text()),
                "hz": float(self.hz_combo.currentText())
            }
            self.config_manager.save_config(filename, self.parameters, settings)

    def on_load_config(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Config", "", "JSON Files (*.json)")
        if filename:
            settings, params = self.config_manager.load_config(filename)
            self.parameters = params
            self.param_table.load_parameters(params)
            self.log.append(f"Config loaded from {filename}")

    def on_browse_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load .dat File", "", "DAT Files (*.dat)")
        if filename:
            try:
                result = self.loader.load_dat(filename)
                if isinstance(result, tuple):
                    # New format with embedded parameters
                    self.dat_buffer, parameters = result
                    if parameters:
                        self.parameters = parameters
                        self.param_table.load_parameters(parameters)
                        self.log.append(f"Loaded {filename} with {len(parameters)} embedded parameters")
                        for param in parameters:
                            self.log.append(f"  - {param.name} (Packet {param.packet_id}, Offset {param.offset})")
                    else:
                        self.log.append(f"Loaded {filename} (no embedded parameters)")
                else:
                    # Old format, binary data only
                    self.dat_buffer = result
                    self.log.append(f"Loaded {filename} (old format - no embedded parameters)")
                    self.log.append("You can add parameters manually using the 'Add Parameter' button")
            except Exception as e:
                self.log.append(f"Error loading file: {str(e)}")

    def on_add_param(self):
        # Open parameter editor dialog for new parameter
        dialog = ParameterEditorDialog(None, self)
        if dialog.exec_() == ParameterEditorDialog.Accepted:
            # Create new parameter with edited values
            new_param = dialog.get_parameter()
            new_param.sl_no = len(self.parameters) + 1
            if not new_param.name:  # If no name provided, give a default
                new_param.name = f"param_{len(self.parameters) + 1}"
            self.parameters.append(new_param)
            self.param_table.parameters_list = self.parameters  # Update reference
            self.param_table.load_parameters(self.parameters)
            self.log.append(f"Added parameter: {new_param.name}")

    def on_edit_param(self):
        # Get selected row
        current_row = self.param_table.currentRow()
        if current_row >= 0 and current_row < len(self.parameters):
            param = self.parameters[current_row]
            # Open parameter editor dialog
            dialog = ParameterEditorDialog(param, self)
            if dialog.exec_() == ParameterEditorDialog.Accepted:
                # Update the parameter with edited values
                edited_param = dialog.get_parameter()
                self.parameters[current_row] = edited_param
                self.param_table.load_parameters(self.parameters)
                self.log.append(f"Updated parameter: {edited_param.name}")
        else:
            self.log.append("Please select a parameter to edit")

    def on_remove_param(self):
        # Get selected row
        current_row = self.param_table.currentRow()
        if current_row >= 0 and current_row < len(self.parameters):
            param = self.parameters.pop(current_row)
            self.param_table.parameters_list = self.parameters  # Update reference
            self.param_table.load_parameters(self.parameters)
            self.log.append(f"Removed parameter: {param.name}")
        else:
            self.log.append("Please select a parameter to remove")

    def on_record_ready(self, record_idx, record_time, packets):
        # Get current time increment based on Hz setting
        hz = float(self.hz_combo.currentText())
        time_increment = 1.0 / hz
        
        # Update GUI with new record data (only plot params within their timing window)
        filtered_params = []
        for p in self.parameters:
            within_start = True if (p.start_time is None) else (record_time >= p.start_time)
            within_end = True if (p.end_time is None) else (record_time <= p.end_time)
            if within_start and within_end:
                filtered_params.append(p)
        self.waveform_plot.update_waveform(filtered_params, record_time, time_increment)
        # Reflect generated record count immediately for responsiveness
        self.records_sent_label.setText(f"Records Sent: {record_idx + 1}")
        
        # Update parameter table with instantaneous values
        for param in self.parameters:
            if param.enabled:
                from core.waveform import make_waveform
                wf = make_waveform(param.waveform, param.freq, param.phase, param.full_sweep)
                
                # Enforce per-parameter timing window for UI updates as well
                within_start = True if (param.start_time is None) else (record_time >= param.start_time)
                within_end = True if (param.end_time is None) else (record_time <= param.end_time)
                if not (within_start and within_end):
                    continue

                if param.samples_per_500ms == 1:  # Major cycle - single value
                    if param.dtype == "float":
                        value = 0.0  # No fixed value UI anymore; keep 0.0 default for float major
                    else:
                        # Bit-major toggles strictly between min and max
                        analog = wf.value(record_time, param.min_v, param.max_v)
                        threshold = (param.min_v + param.max_v) / 2.0
                        value = param.min_v if analog < threshold else param.max_v
                    self.param_table.update_instantaneous(param.name, value, record_time, time_increment)
                else:  # Minor cycle - 5 samples
                    # Calculate all 5 sample values with correct spacing
                    sample_values = []
                    sample_spacing = time_increment / 5.0
                    for i in range(5):
                        sample_time = record_time + i * sample_spacing
                        value = wf.value(sample_time, param.min_v, param.max_v)
                        sample_values.append(value)
                    
                    # Update table with all 5 values
                    self.param_table.update_instantaneous(param.name, sample_values, record_time, time_increment)

    def update_current_time(self, record_idx, record_time, packets):
        """Update current time from seeder thread"""
        self.current_time_label.setText(f"Current Time: {record_time:.1f} sec")

    def update_records_sent(self, record_idx, time):
        """Update records sent count from sender thread"""
        self.records_sent_label.setText(f"Records Sent: {record_idx + 1}")
