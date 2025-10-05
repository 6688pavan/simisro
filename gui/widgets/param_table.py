from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QCheckBox
from PyQt5.QtCore import Qt

class ParameterTableWidget(QTableWidget):
    HEADERS = ["S.No", "Show in Graph", "Name", "Packet ID", "Type", "Offset", "Length", "Inst. Value", "Time"]

    def __init__(self, parameters_list=None):
        super().__init__(0, len(self.HEADERS))
        self.setHorizontalHeaderLabels(self.HEADERS)
        self.parameters_list = parameters_list

    def load_parameters(self, params):
        self.setRowCount(0)
        for param in params:
            self.add_parameter(param)

    def add_parameter(self, param):
        r = self.rowCount()
        self.insertRow(r)
        if param.dtype == "float":
            length = 4 * param.samples_per_500ms  # 4 bytes per sample
        else:  # Digital
            length = (param.bit_width // 8 if param.samples_per_500ms == 1 else 8) * param.samples_per_500ms
        values = [
            QTableWidgetItem(str(getattr(param, 'sl_no', r + 1))),
            QTableWidgetItem(""),  # Placeholder for checkbox widget
            QTableWidgetItem(param.name),
            QTableWidgetItem(str(param.packet_id)),
            QTableWidgetItem(param.dtype),
            QTableWidgetItem(str(param.offset)),
            QTableWidgetItem(str(length)),
            QTableWidgetItem(""),
            QTableWidgetItem("")
        ]
        for c, item in enumerate(values):
            self.setItem(r, c, item)
        # Make S.No non-editable
        sn_item = self.item(r, 0)
        if sn_item:
            sn_item.setFlags(sn_item.flags() & ~Qt.ItemIsEditable)
        checkbox = QCheckBox()
        checkbox.setChecked(param.enabled_in_graph)
        checkbox.stateChanged.connect(lambda state, row=r: self._update_graph_enable(row, state))
        self.setCellWidget(r, 1, checkbox)

    def _update_graph_enable(self, row, state):
        # Update parameter enabled_in_graph state
        if self.parameters_list and row < len(self.parameters_list):
            self.parameters_list[row].enabled_in_graph = bool(state)
            param_name = self.item(row, 2).text() if self.item(row, 2) else "Unknown"
            print(f"Parameter {param_name} graph enabled: {bool(state)}")

    def update_instantaneous(self, name, value, t, time_increment=1.0):
        """Update instantaneous value and time for a parameter (major cycle or minor cycle)"""
        for r in range(self.rowCount()):
            if self.item(r, 2) and self.item(r, 2).text() == name:
                if isinstance(value, list):  # Minor cycle
                    values_text = " | ".join([f"{v:.4g}" for v in value])
                    sample_spacing = time_increment / 5.0  # Spread 5 samples across the time increment
                    times_text = " | ".join([f"{t + i*sample_spacing:.3f}" for i in range(5)])
                    self.setItem(r, 7, QTableWidgetItem(values_text))
                    self.setItem(r, 8, QTableWidgetItem(times_text))
                else:  # Major cycle
                    self.setItem(r, 7, QTableWidgetItem(f"{value:.4g}"))
                    self.setItem(r, 8, QTableWidgetItem(f"{t:.3f}"))
                break