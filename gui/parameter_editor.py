from PyQt5.QtWidgets import QDialog, QTabWidget, QVBoxLayout, QWidget, QFormLayout, QLineEdit, QSpinBox, QComboBox, QCheckBox, QDoubleSpinBox, QPushButton, QHBoxLayout
from core.models import Parameter
from gui.widgets.waveform_plot import WaveformPlotWidget
from core.waveform import *

class ParameterEditorWindow(QDialog):
    def __init__(self, param=None):
        super().__init__()
        self.setWindowTitle("Parameter Editor")
        self.param = param or Parameter("", 0, 0, 0, "float")
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        self.setup_tabs()
        btn_lay = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        btn_lay.addWidget(ok_btn)
        btn_lay.addWidget(cancel_btn)
        layout.addLayout(btn_lay)
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

    def setup_tabs(self):
        # Tab 1: Basic Settings
        tab1 = QWidget()
        form1 = QFormLayout()
        self.name_edit = QLineEdit(self.param.name)
        form1.addRow("Name", self.name_edit)
        self.sl_no_spin = QSpinBox()
        self.sl_no_spin.setValue(self.param.sl_no)
        form1.addRow("sl.no", self.sl_no_spin)
        self.packet_id_spin = QSpinBox()
        self.packet_id_spin.setValue(self.param.packet_id)
        form1.addRow("Packet ID", self.packet_id_spin)
        self.offset_spin = QSpinBox()
        self.offset_spin.setRange(0, 1399)
        self.offset_spin.setValue(self.param.offset)
        form1.addRow("Offset", self.offset_spin)
        self.type_combo = QComboBox()
        self.type_combo.addItems(["float", "bit"])
        self.type_combo.setCurrentText(self.param.dtype)
        form1.addRow("Type", self.type_combo)
        self.enabled_check = QCheckBox()
        self.enabled_check.setChecked(self.param.enabled)
        form1.addRow("Enabled by default", self.enabled_check)
        self.samples_spin = QSpinBox()
        self.samples_spin.setValue(self.param.samples_per_500ms)
        form1.addRow("Samples per 500ms", self.samples_spin)
        tab1.setLayout(form1)
        self.tab_widget.addTab(tab1, "Basic Settings")

        # Tab 2: Waveform Settings
        tab2 = QWidget()
        form2 = QFormLayout()
        self.wave_type_combo = QComboBox()
        self.wave_type_combo.addItems(["Sine", "Cosine", "Triangle", "Square", "Step", "Noise"])
        self.wave_type_combo.setCurrentText(self.param.waveform_settings.get('type', 'Sine'))
        form2.addRow("Waveform Type", self.wave_type_combo)
        self.freq_spin = QDoubleSpinBox()
        self.freq_spin.setValue(self.param.waveform_settings.get('frequency', 1.0))
        form2.addRow("Frequency (Hz)", self.freq_spin)
        self.phase_spin = QDoubleSpinBox()
        self.phase_spin.setValue(self.param.waveform_settings.get('phase', 0.0))
        form2.addRow("Phase (radians)", self.phase_spin)
        self.min_spin = QDoubleSpinBox()
        self.min_spin.setValue(self.param.min_val)
        form2.addRow("Min", self.min_spin)
        self.max_spin = QDoubleSpinBox()
        self.max_spin.setValue(self.param.max_val)
        form2.addRow("Max", self.max_spin)
        self.full_sweep_check = QCheckBox()
        self.full_sweep_check.setChecked(self.param.full_sweep)
        form2.addRow("Full Sweep", self.full_sweep_check)
        self.amplitude_spin = QDoubleSpinBox()
        self.amplitude_spin.setValue(self.param.waveform_settings.get('amplitude', (self.param.max_val - self.param.min_val) / 2))
        form2.addRow("Amplitude", self.amplitude_spin)
        self.offset_val_spin = QDoubleSpinBox()
        self.offset_val_spin.setValue(self.param.waveform_settings.get('offset', (self.param.max_val + self.param.min_val) / 2))
        form2.addRow("Offset", self.offset_val_spin)
        def toggle_fields(state):
            enabled = state == 0  # Disable if full_sweep checked
            self.amplitude_spin.setEnabled(enabled)
            self.offset_val_spin.setEnabled(enabled)
        self.full_sweep_check.stateChanged.connect(toggle_fields)
        toggle_fields(2 if self.full_sweep_check.isChecked() else 0)  # Qt.Checked = 2
        tab2.setLayout(form2)
        self.tab_widget.addTab(tab2, "Waveform Settings")

        # Tab 3: Preview
        tab3 = QWidget()
        vlay = QVBoxLayout()
        self.preview_plot = WaveformPlotWidget()
        vlay.addWidget(self.preview_plot)
        self.generate_preview_btn = QPushButton("Generate Preview")
        vlay.addWidget(self.generate_preview_btn)
        tab3.setLayout(vlay)
        self.tab_widget.addTab(tab3, "Preview")
        self.generate_preview_btn.clicked.connect(self.generate_preview)

    def generate_preview(self):
        wave_type = self.wave_type_combo.currentText()
        freq = self.freq_spin.value()
        phase = self.phase_spin.value()
        min_val = self.min_spin.value()
        max_val = self.max_spin.value()
        full_sweep = self.full_sweep_check.isChecked()
        amplitude = self.amplitude_spin.value()
        offset_val = self.offset_val_spin.value()
        if wave_type == 'Sine':
            gen = SineGenerator(freq, phase)
        elif wave_type == 'Cosine':
            gen = CosineGenerator(freq, phase)
        elif wave_type == 'Triangle':
            gen = TriangleGenerator(freq, phase)
        elif wave_type == 'Square':
            gen = SquareGenerator(freq, phase)
        elif wave_type == 'Step':
            gen = StepGenerator(freq, phase)
        elif wave_type == 'Noise':
            gen = NoiseGenerator()
        else:
            return
        sample_count = 100
        t_array = [i * 10.0 / (sample_count - 1) for i in range(sample_count)]
        normalized = gen.values(t_array)
        values = []
        for norm in normalized:
            if full_sweep:
                amp = (max_val - min_val) / 2
                off = (max_val + min_val) / 2
            else:
                amp = amplitude
                off = offset_val
            val = off + amp * norm
            values.append(val)
        self.preview_plot.clear()
        self.preview_plot.plot(t_array, values, pen='b')

    def get_parameter(self):
        return Parameter(
            name=self.name_edit.text(),
            sl_no=self.sl_no_spin.value(),
            packet_id=self.packet_id_spin.value(),
            offset=self.offset_spin.value(),
            dtype=self.type_combo.currentText(),
            enabled=self.enabled_check.isChecked(),
            min_val=self.min_spin.value(),
            max_val=self.max_spin.value(),
            waveform_settings={
                'type': self.wave_type_combo.currentText(),
                'frequency': self.freq_spin.value(),
                'phase': self.phase_spin.value(),
                'amplitude': self.amplitude_spin.value(),
                'offset': self.offset_val_spin.value()
            },
            samples_per_500ms=self.samples_spin.value(),
            full_sweep=self.full_sweep_check.isChecked()
        )