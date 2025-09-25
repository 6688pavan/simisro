from PyQt5.QtWidgets import QMainWindow, QSplitter, QHBoxLayout, QVBoxLayout, QWidget, QGroupBox, QPushButton, QLineEdit, QDoubleSpinBox, QLabel, QFileDialog, QSpinBox
from PyQt5.QtCore import Qt
from gui.widgets.param_table import ParameterTableWidget
from gui.widgets.waveform_plot import WaveformPlotWidget
from gui.widgets.log_view import LogViewWidget
from gui.parameter_editor import ParameterEditorWindow
from threads.seeder_thread import SeederThread
from threads.sender_thread import SenderThread
from core.models import ParameterList, RecordSpec
from core.seeder import SeedingEngine
from core.multicast_sender import MulticastSender
from utils.io_helpers import load_parameters_from_file
from utils.json_helpers import save_config, load_config
from threads.worker_signals import WorkerSignals

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Telemetry Simulator")
        self.parameter_list = ParameterList()
        self.record_spec = RecordSpec()
        self.signals = WorkerSignals()
        self.seeding_engine = SeedingEngine(self.parameter_list, self.record_spec, self.signals)
        self.multicast_sender = MulticastSender("239.0.0.1", 12345)
        # Threads will be created in setup_threads so they can be recreated on Reset
        self.seeder_thread = None
        self.sender_thread = None
        self.bytes_sent = 0
        self.setup_ui()
        self.setup_threads()
        self.connect_signals()

    def setup_ui(self):
        central = QWidget()
        main_lay = QVBoxLayout()
        central.setLayout(main_lay)
        self.setCentralWidget(central)

        # Top layout
        top_lay = QHBoxLayout()
        main_lay.addLayout(top_lay)

        # Controls
        controls_group = QGroupBox("Controls")
        controls_lay = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.pause_btn = QPushButton("Pause")
        self.resume_btn = QPushButton("Resume")
        self.stop_btn = QPushButton("Stop")
        self.reset_btn = QPushButton("Reset")
        controls_lay.addWidget(self.start_btn)
        controls_lay.addWidget(self.pause_btn)
        controls_lay.addWidget(self.resume_btn)
        controls_lay.addWidget(self.stop_btn)
        controls_lay.addWidget(self.reset_btn)
        controls_group.setLayout(controls_lay)
        top_lay.addWidget(controls_group)

        # Config
        config_group = QGroupBox("Config")
        config_lay = QHBoxLayout()
        self.export_btn = QPushButton("Export JSON")
        self.load_btn = QPushButton("Load Config")
        config_lay.addWidget(self.export_btn)
        config_lay.addWidget(self.load_btn)
        config_group.setLayout(config_lay)
        top_lay.addWidget(config_group)

        # File Loader
        file_group = QGroupBox("File Loader")
        file_lay = QHBoxLayout()
        self.browse_btn = QPushButton("Browse")
        self.file_label = QLabel("No file")
        file_lay.addWidget(self.browse_btn)
        file_lay.addWidget(self.file_label)
        file_group.setLayout(file_lay)
        top_lay.addWidget(file_group)

        # Time
        time_group = QGroupBox("Time")
        time_lay = QHBoxLayout()
        time_lay.addWidget(QLabel("Start:"))
        self.start_edit = QLineEdit("-900.0")
        time_lay.addWidget(self.start_edit)
        time_lay.addWidget(QLabel("End:"))
        self.end_edit = QLineEdit("1200.0")
        time_lay.addWidget(self.end_edit)
        time_group.setLayout(time_lay)
        top_lay.addWidget(time_group)

        # Hz
        hz_group = QGroupBox("Transmission Hz")
        hz_lay = QHBoxLayout()
        hz_lay.addWidget(QLabel("Hz:"))
        self.hz_spin = QDoubleSpinBox()
        self.hz_spin.setValue(2.0)
        hz_lay.addWidget(self.hz_spin)
        hz_group.setLayout(hz_lay)
        top_lay.addWidget(hz_group)

        # Stats
        stats_group = QGroupBox("Live Stats")
        stats_lay = QHBoxLayout()
        self.current_time_label = QLabel("Current Time: 0")
        self.records_sent_label = QLabel("Records Sent: 0")
        self.bytes_sent_label = QLabel("Bytes Sent: 0")
        self.packets_per_record_label = QLabel("Packets/Record: 10")
        stats_lay.addWidget(self.current_time_label)
        stats_lay.addWidget(self.records_sent_label)
        stats_lay.addWidget(self.bytes_sent_label)
        stats_lay.addWidget(self.packets_per_record_label)
        stats_group.setLayout(stats_lay)

        # Network
        net_group = QGroupBox("Network")
        net_lay = QHBoxLayout()
        net_lay.addWidget(QLabel("Multicast IP:"))
        self.multicast_ip_edit = QLineEdit("239.0.0.1")
        net_lay.addWidget(self.multicast_ip_edit)
        net_lay.addWidget(QLabel("Port:"))
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(12345)
        net_lay.addWidget(self.port_spin)
        net_group.setLayout(net_lay)

        # Stack Live Stats and Network vertically (one below the other)
        stats_net_widget = QWidget()
        stats_net_layout = QVBoxLayout()
        stats_net_layout.setContentsMargins(0, 0, 0, 0)
        stats_net_layout.addWidget(stats_group)
        stats_net_layout.addWidget(net_group)
        stats_net_widget.setLayout(stats_net_layout)
        top_lay.addWidget(stats_net_widget)

        # Middle splitter
        splitter = QSplitter(Qt.Horizontal)
        main_lay.addWidget(splitter)

        # Left: Parameter table
        left_widget = QWidget()
        left_lay = QVBoxLayout()
        left_widget.setLayout(left_lay)
        self.param_table = ParameterTableWidget(self)
        left_lay.addWidget(self.param_table)
        btn_lay = QHBoxLayout()
        self.add_param_btn = QPushButton("Add Parameter")
        self.remove_param_btn = QPushButton("Remove Parameter")
        self.edit_param_btn = QPushButton("Edit Parameter")
        btn_lay.addWidget(self.add_param_btn)
        btn_lay.addWidget(self.remove_param_btn)
        btn_lay.addWidget(self.edit_param_btn)
        left_lay.addLayout(btn_lay)
        splitter.addWidget(left_widget)

        # Right: Waveform plot (containerized for proper sizing)
        waveform_container = QWidget()
        waveform_layout = QVBoxLayout()
        waveform_layout.setContentsMargins(0, 0, 0, 0)
        self.waveform_plot = WaveformPlotWidget()
        waveform_layout.addWidget(self.waveform_plot)
        waveform_container.setLayout(waveform_layout)
        splitter.addWidget(waveform_container)

        # Bottom: Log view
        self.log_view = LogViewWidget()
        main_lay.addWidget(self.log_view)

    def connect_signals(self):
        self.start_btn.clicked.connect(self.start_simulation)
        # Use lambdas so the currently assigned thread instance is used (supports recreation)
        self.pause_btn.clicked.connect(lambda: self.seeder_thread.pause() if self.seeder_thread is not None else None)
        self.resume_btn.clicked.connect(lambda: self.seeder_thread.resume() if self.seeder_thread is not None else None)
        self.stop_btn.clicked.connect(self.stop_simulation)
        self.reset_btn.clicked.connect(self.reset_simulation)
        self.export_btn.clicked.connect(self.export_json)
        self.load_btn.clicked.connect(self.load_config)
        self.browse_btn.clicked.connect(self.load_file)
        self.add_param_btn.clicked.connect(self.add_parameter)
        self.remove_param_btn.clicked.connect(self.remove_parameter)
        self.edit_param_btn.clicked.connect(self.edit_parameter)

        # Note: thread signal wiring is done in setup_threads so threads may be recreated
        self.signals.sample_generated.connect(self.update_plot_and_table)
        self.signals.error.connect(lambda msg: self.log_view.add_log(msg, "ERROR"))

    def start_simulation(self):
        # Do not start simulation without parameters
        if not self.parameter_list.parameters:
            self.log_view.add_log("Cannot start simulation: no parameters loaded", "ERROR")
            return

        # Ensure threads exist (recreate if needed)
        if self.seeder_thread is None or self.sender_thread is None:
            self.setup_threads()

        # Prevent starting if already running
        try:
            if getattr(self.seeder_thread, 'isRunning', lambda: False)() and self.seeder_thread.isRunning():
                self.log_view.add_log("Simulation already running", "WARNING")
                return
        except Exception:
            pass

        try:
            self.seeder_thread.start_time = float(self.start_edit.text())
            self.seeder_thread.end_time = float(self.end_edit.text())
            self.seeder_thread.hz = self.hz_spin.value()
            self.seeder_thread.interval = int(1000 / self.seeder_thread.hz)
            ip = self.multicast_ip_edit.text()
            port = self.port_spin.value()
            self.multicast_sender.close()
            self.multicast_sender = MulticastSender(ip, port)
            self.sender_thread.multicast_sender = self.multicast_sender
            self.seeder_thread.start()
            self.sender_thread.start()
            self.log_view.add_log("Simulation started", "INFO")
        except ValueError as e:
            self.log_view.add_log(str(e), "ERROR")

    def stop_simulation(self):
        if self.seeder_thread is not None:
            self.seeder_thread.stop()
        if self.sender_thread is not None:
            self.sender_thread.stop()
        self.multicast_sender.close()
        # Clear references so future starts recreate threads
        self.seeder_thread = None
        self.sender_thread = None
        self.log_view.add_log("Simulation stopped and resources cleaned", "INFO")

    def setup_threads(self):
        """Create thread instances and wire their signals. Safe to call to recreate threads after stop/reset."""
        # If existing threads exist, ensure they're stopped
        if self.seeder_thread is not None:
            try:
                self.seeder_thread.stop()
            except Exception:
                pass
        if self.sender_thread is not None:
            try:
                self.sender_thread.stop()
            except Exception:
                pass

        # create fresh thread objects
        self.seeder_thread = SeederThread(self.seeding_engine)
        self.sender_thread = SenderThread(self.multicast_sender)

        # wire inter-thread signals
        self.seeder_thread.signals.record_ready.connect(self.sender_thread.on_record_ready)
        self.sender_thread.signals.record_sent.connect(self.update_stats)
        self.seeder_thread.signals.log_message.connect(self.log_view.add_log)
        self.sender_thread.signals.log_message.connect(self.log_view.add_log)
        self.sender_thread.signals.error.connect(lambda msg: self.log_view.add_log(msg, "ERROR"))

    def reset_simulation(self):
        """Stop any running threads, reset UI fields and recreate thread objects so the simulation can start fresh."""
        # Stop threads
        if self.seeder_thread is not None:
            try:
                self.seeder_thread.stop()
            except Exception:
                pass
        if self.sender_thread is not None:
            try:
                self.sender_thread.stop()
            except Exception:
                pass

        # Reset network to defaults
        self.multicast_ip_edit.setText("239.0.0.1")
        self.port_spin.setValue(12345)
        # Reset time/config fields
        self.start_edit.setText("-900.0")
        self.end_edit.setText("1200.0")
        self.hz_spin.setValue(2.0)

        # Reset stats
        self.current_time_label.setText("Current Time: 0")
        self.records_sent_label.setText("Records Sent: 0")
        self.bytes_sent = 0
        self.bytes_sent_label.setText("Bytes Sent: 0")

        # Recreate threads and re-wire signals
        self.setup_threads()

        self.log_view.add_log("Simulation reset to defaults", "INFO")

    def update_stats(self, record_idx):
        self.current_time_label.setText(f"Current Time: {self.seeder_thread.current_time:.1f}")
        self.records_sent_label.setText(f"Records Sent: {record_idx + 1}")
        self.bytes_sent += 1400 * 10  # approx per record
        self.bytes_sent_label.setText(f"Bytes Sent: {self.bytes_sent}")

    def update_plot_and_table(self, param_name, sample_time, value):
        self.param_table.update_instantaneous(param_name, value, sample_time)
        self.waveform_plot.update_curve(param_name, sample_time, value)

    def export_json(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Export JSON", "", "JSON (*.json)")
        if filename:
            config = self.parameter_list.to_dict()
            save_config(filename, config)
            self.log_view.add_log(f"Config exported to {filename}", "INFO")

    def load_config(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Config", "", "JSON (*.json)")
        if filename:
            config = load_config(filename)
            self.parameter_list = ParameterList.from_dict(config)
            self.param_table.update_table(self.parameter_list.parameters)
            self.log_view.add_log(f"Config loaded from {filename}", "INFO")

    def load_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load File", "", "CSV or Binary (*.csv *.bin)")
        if filename:
            self.file_label.setText(filename)
            try:
                params = load_parameters_from_file(filename)
                self.parameter_list.parameters = params
                self.param_table.update_table(params)
                # Ensure waveform plot has curves for enabled parameters
                for p in params:
                    self.waveform_plot.add_parameter_curve(p)
                    # Set marker/curve visibility according to parameter
                    self.waveform_plot.toggle_curve(p.name, p.enabled)
                self.log_view.add_log(f"Parameters loaded from {filename}", "INFO")
            except Exception as e:
                self.log_view.add_log(str(e), "ERROR")

    def add_parameter(self):
        editor = ParameterEditorWindow()
        if editor.exec_():
            param = editor.get_parameter()
            self.parameter_list.add(param)
            self.param_table.add_row(param)
            self.waveform_plot.add_parameter_curve(param)
            self.log_view.add_log(f"Added parameter {param.name}", "INFO")

    def remove_parameter(self):
        row = self.param_table.currentRow()
        if row >= 0:
            name = self.param_table.item(row, 1).text()
            del self.parameter_list.parameters[row]
            self.param_table.removeRow(row)
            self.waveform_plot.remove_curve(name)
            self.log_view.add_log(f"Removed parameter {name}", "INFO")

    def edit_parameter(self):
        row = self.param_table.currentRow()
        if row >= 0:
            param = self.parameter_list.parameters[row]
            editor = ParameterEditorWindow(param)
            if editor.exec_():
                new_param = editor.get_parameter()
                self.parameter_list.parameters[row] = new_param
                self.param_table.update_row(row, new_param)
                self.waveform_plot.update_curve_settings(new_param)  # Assume method to refresh
                self.log_view.add_log(f"Edited parameter {new_param.name}", "INFO")