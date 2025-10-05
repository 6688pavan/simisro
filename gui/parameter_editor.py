from PyQt5.QtWidgets import (QDialog, QTabWidget, QVBoxLayout, QWidget, QFormLayout, 
                             QLineEdit, QSpinBox, QComboBox, QCheckBox, QDoubleSpinBox, 
                             QPushButton, QHBoxLayout, QGroupBox, QLabel)
import math
from core.models import Parameter

class ParameterEditorDialog(QDialog):
    def __init__(self, param=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Parameter Editor")
        self.param = param
        self.setModal(True)
        self.setup_ui()
        self.apply_grey_theme()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Setup tabs
        self.setup_basic_tab()
        self.setup_waveform_tab()
        self.setup_timing_tab()
        
        # Buttons
        button_layout = QHBoxLayout()
        self.preview_btn = QPushButton("Preview (10s)")
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        button_layout.addWidget(self.preview_btn)
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        self.preview_btn.clicked.connect(self.preview_parameter)
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
        # Initialize bit width visibility
        self._on_cycle_changed(self.cycle_combo.currentText())

    def apply_grey_theme(self):
        """Apply grey color scheme to parameter editor"""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTabWidget {
                background-color: #2b2b2b;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #3c3c3c;
            }
            QTabBar::tab {
                background-color: #4a4a4a;
                border: 1px solid #555555;
                padding: 8px 12px;
                margin-right: 2px;
                color: #ffffff;
            }
            QTabBar::tab:selected {
                background-color: #3c3c3c;
                border-bottom: 2px solid #666666;
            }
            QTabBar::tab:hover {
                background-color: #5a5a5a;
            }
            QPushButton {
                background-color: #4a4a4a;
                border: 1px solid #666666;
                border-radius: 3px;
                padding: 8px 16px;
                color: #ffffff;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
                border: 1px solid #777777;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
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
            QSpinBox, QDoubleSpinBox {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
                color: #ffffff;
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
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

    def setup_basic_tab(self):
        """Setup the basic parameter settings tab"""
        tab = QWidget()
        form = QFormLayout()
        
        # Name
        self.name_edit = QLineEdit(self.param.name if self.param else "")
        form.addRow("Name:", self.name_edit)
        
        # Serial number intentionally omitted from editor; it is displayed in the table only
        
        # Packet ID
        self.packet_id_spin = QSpinBox()
        self.packet_id_spin.setRange(0, 9)
        self.packet_id_spin.setValue(self.param.packet_id if self.param else 0)
        form.addRow("Packet ID:", self.packet_id_spin)
        
        # Offset
        self.offset_spin = QSpinBox()
        self.offset_spin.setRange(0, 1399)
        self.offset_spin.setValue(self.param.offset if self.param else 0)
        form.addRow("Offset:", self.offset_spin)
        
        # Cycle type (bundled with data type)
        self.cycle_combo = QComboBox()
        self.cycle_combo.addItems(["Major (1 sample) - Bit", "Minor (5 samples) - Float"])
        if self.param and self.param.samples_per_500ms == 5:
            self.cycle_combo.setCurrentIndex(1)
        else:
            self.cycle_combo.setCurrentIndex(0)
        self.cycle_combo.currentTextChanged.connect(self._on_cycle_changed)
        form.addRow("Cycle Type:", self.cycle_combo)
        
        # Bit width (for major cycle/bit parameters)
        self.bit_width_spin = QSpinBox()
        self.bit_width_spin.setRange(8, 32)
        self.bit_width_spin.setSingleStep(8)
        self.bit_width_spin.setValue(self.param.bit_width if self.param else 8)
        self.bit_width_label = QLabel("Bit Width:")
        form.addRow(self.bit_width_label, self.bit_width_spin)
        
        # Show in Graph checkbox
        self.graph_check = QCheckBox()
        self.graph_check.setChecked(self.param.enabled_in_graph if self.param else False)
        form.addRow("Show in Graph:", self.graph_check)
        
        tab.setLayout(form)
        self.tab_widget.addTab(tab, "Basic Settings")
    
    def setup_waveform_tab(self):
        """Setup the waveform settings tab"""
        tab = QWidget()
        form = QFormLayout()
        
        # Waveform type
        self.waveform_combo = QComboBox()
        self.waveform_combo.addItems(["Sine", "Triangle", "Square", "Step", "Noise"])
        self.waveform_combo.setCurrentText(self.param.waveform if self.param else "Sine")
        form.addRow("Waveform:", self.waveform_combo)
        
        # Frequency
        self.freq_spin = QDoubleSpinBox()
        self.freq_spin.setRange(0.01, 100.0)
        self.freq_spin.setDecimals(2)
        self.freq_spin.setValue(self.param.freq if self.param else 1.0)
        form.addRow("Frequency (Hz):", self.freq_spin)
        
        # Phase
        self.phase_spin = QDoubleSpinBox()
        self.phase_spin.setRange(-360.0, 360.0)
        self.phase_spin.setDecimals(1)
        # Add a small phase offset by default to make values more visible
        default_phase = self.param.phase if self.param else 45.0  # 45 degrees offset
        self.phase_spin.setValue(default_phase)
        form.addRow("Phase (degrees):", self.phase_spin)
        
        # Min/Max values
        self.min_spin = QDoubleSpinBox()
        self.min_spin.setRange(-10000.0, 10000.0)
        self.min_spin.setDecimals(3)
        self.min_spin.setValue(self.param.min_v if self.param else 0.0)
        form.addRow("Min Value:", self.min_spin)
        
        self.max_spin = QDoubleSpinBox()
        self.max_spin.setRange(-10000.0, 10000.0)
        self.max_spin.setDecimals(3)
        self.max_spin.setValue(self.param.max_v if self.param else 1.0)
        form.addRow("Max Value:", self.max_spin)
        
        # Full sweep
        self.full_sweep_check = QCheckBox()
        self.full_sweep_check.setChecked(self.param.full_sweep if self.param else True)
        form.addRow("Full Sweep:", self.full_sweep_check)
        
        # For bit-major, value toggles strictly between Min and Max; no fixed value control
        
        tab.setLayout(form)
        self.tab_widget.addTab(tab, "Waveform")
    
    def setup_timing_tab(self):
        """Setup the timing settings tab"""
        tab = QWidget()
        form = QFormLayout()
        
        # Start time
        self.start_time_spin = QDoubleSpinBox()
        self.start_time_spin.setRange(-10000.0, 10000.0)
        self.start_time_spin.setDecimals(1)
        self.start_time_spin.setValue(self.param.start_time if self.param and self.param.start_time is not None else -900.0)
        form.addRow("Start Time (s):", self.start_time_spin)
        
        # End time
        self.end_time_spin = QDoubleSpinBox()
        self.end_time_spin.setRange(-10000.0, 10000.0)
        self.end_time_spin.setDecimals(1)
        self.end_time_spin.setValue(self.param.end_time if self.param and self.param.end_time is not None else 1200.0)
        form.addRow("End Time (s):", self.end_time_spin)
        
        tab.setLayout(form)
        self.tab_widget.addTab(tab, "Timing")
    
    def _on_cycle_changed(self, cycle_text):
        """Handle cycle type change to show/hide bit width controls"""
        is_major = "Major" in cycle_text
        self.bit_width_label.setVisible(is_major)
        self.bit_width_spin.setVisible(is_major)
    
    def preview_parameter(self):
        """Preview the parameter for 10 seconds"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
        from PyQt5.QtCore import QTimer
        import pyqtgraph as pg
        from core.waveform import make_waveform
        import time
        
        # Create preview dialog
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle("Parameter Preview")
        preview_dialog.setGeometry(200, 200, 600, 400)
        
        layout = QVBoxLayout(preview_dialog)
        
        # Create plot widget
        plot_widget = pg.PlotWidget()
        plot_widget.setBackground('k')
        plot_widget.showGrid(x=True, y=True)
        plot_widget.setLabel('left', 'Value')
        plot_widget.setLabel('bottom', 'Time (s)')
        layout.addWidget(plot_widget)
        
        # Add close button
        close_btn = QPushButton("Close Preview")
        close_btn.clicked.connect(preview_dialog.accept)
        layout.addWidget(close_btn)
        
        # Get current parameter settings
        cycle_type = self.cycle_combo.currentIndex()
        samples_per_500ms = 1 if cycle_type == 0 else 5
        dtype = "bit" if cycle_type == 0 else "float"
        
        # Create waveform
        waveform_type = self.waveform_combo.currentText()
        freq = self.freq_spin.value()
        phase = self.phase_spin.value() * math.pi / 180.0
        full_sweep = self.full_sweep_check.isChecked()
        
        wf = make_waveform(waveform_type, freq, phase, full_sweep)
        min_v = self.min_spin.value()
        max_v = self.max_spin.value()
        
        # Generate preview data
        time_data = []
        value_data = []
        
        start_time = 0.0
        duration = 10.0  # 10 seconds
        sample_rate = 10.0  # 10 samples per second
        
        for i in range(int(duration * sample_rate)):
            t = start_time + i / sample_rate
            value = wf.value(t, min_v, max_v)
            time_data.append(t)
            value_data.append(value)
        
        # Plot the data
        plot_widget.plot(time_data, value_data, pen=pg.mkPen(color='cyan', width=2), 
                        symbol='o', symbolSize=4, symbolBrush='cyan')
        
        # Show the dialog
        preview_dialog.exec_()
    
    def get_parameter(self):
        cycle_type = self.cycle_combo.currentIndex()
        samples_per_500ms = 1 if cycle_type == 0 else 5
        dtype = "bit" if cycle_type == 0 else "float"  # Major = bit, Minor = float
        
        return Parameter(
            name=self.name_edit.text(),
            packet_id=self.packet_id_spin.value(),
            offset=self.offset_spin.value(),
            dtype=dtype,
            min_v=self.min_spin.value(),
            max_v=self.max_spin.value(),
            waveform=self.waveform_combo.currentText(),
            freq=self.freq_spin.value(),
            phase=self.phase_spin.value() * math.pi / 180.0,  # Convert degrees to radians
            full_sweep=self.full_sweep_check.isChecked(),
            samples_per_500ms=samples_per_500ms,
            enabled_in_graph=self.graph_check.isChecked(),
            enabled=True,  # All parameters are enabled by default
            start_time=self.start_time_spin.value(),
            end_time=self.end_time_spin.value(),
            fixed_value=None,
            bit_width=self.bit_width_spin.value()
        )