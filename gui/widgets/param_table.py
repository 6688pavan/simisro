from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QCheckBox
from PyQt5.QtCore import Qt

class ParameterTableWidget(QTableWidget):
    HEADERS = ["S.No", "Show in Graph", "Enabled", "Name", "Packet ID", "Type", "Offset", "Length", "Inst. Value", "Time"]

    def __init__(self, parameters_list=None):
        super().__init__(0, len(self.HEADERS))
        self.setHorizontalHeaderLabels(self.HEADERS)
        self.parameters_list = parameters_list
        # Hash map for O(1) parameter name lookup: name -> row_index
        self.name_to_row = {}

    def load_parameters(self, params):
        self.setRowCount(0)
        self.name_to_row.clear()  # Clear the hash map
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
            QTableWidgetItem(""),  # Placeholder for graph checkbox
            QTableWidgetItem(""),  # Placeholder for enabled checkbox
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
        graph_checkbox = QCheckBox()
        graph_checkbox.setChecked(param.enabled_in_graph)
        graph_checkbox.stateChanged.connect(lambda state, row=r: self._update_graph_enable(row, state))
        # Graph checkbox availability depends on Enabled state
        graph_checkbox.setEnabled(bool(param.enabled))
        self.setCellWidget(r, 1, graph_checkbox)

        enabled_checkbox = QCheckBox()
        enabled_checkbox.setChecked(param.enabled)
        enabled_checkbox.stateChanged.connect(lambda state, row=r: self._update_enabled(row, state))
        self.setCellWidget(r, 2, enabled_checkbox)
        
        # Add to hash map for O(1) lookup
        self.name_to_row[param.name] = r

    def _update_graph_enable(self, row, state):
        # Update parameter enabled_in_graph state
        if self.parameters_list and row < len(self.parameters_list):
            self.parameters_list[row].enabled_in_graph = bool(state)
            param_name = self.item(row, 3).text() if self.item(row, 3) else "Unknown"
            print(f"DEBUG: Parameter {param_name} graph enabled: {bool(state)} (row {row})")
            print(f"DEBUG: Parameter object enabled_in_graph: {self.parameters_list[row].enabled_in_graph}")

    def _update_enabled(self, row, state):
        # Update parameter enabled state
        if self.parameters_list and row < len(self.parameters_list):
            self.parameters_list[row].enabled = bool(state)
            # Enable/disable the graph checkbox accordingly
            graph_checkbox = self.cellWidget(row, 1)
            if isinstance(graph_checkbox, QCheckBox):
                graph_checkbox.setEnabled(bool(state))
                if not bool(state):
                    # Also uncheck when disabled to reflect non-participation
                    graph_checkbox.setChecked(False)
            param_name = self.item(row, 3).text() if self.item(row, 3) else "Unknown"
            print(f"Parameter {param_name} enabled: {bool(state)}")

    def update_instantaneous(self, name, value, t, time_increment=1.0):
        """Update instantaneous value and time for a parameter (major cycle or minor cycle).

        If minor-cycle values are provided along with an explicit list of sample times,
        the provided times will be displayed verbatim. Otherwise, times will be
        reconstructed using the given time_increment.
        """
        # O(1) hash lookup instead of O(n) linear search
        if name not in self.name_to_row:
            return  # Parameter not found
        
        r = self.name_to_row[name]
        if isinstance(value, list):  # Minor cycle
            values_text = " | ".join([f"{v:.4g}" for v in value])
            # If t is a list of times matching value count, use it directly
            if isinstance(t, list) and len(t) == len(value):
                times_text = " | ".join([f"{ti:.3f}" for ti in t])
            else:
                sample_spacing = time_increment / 5.0
                times_text = " | ".join([f"{t + i*sample_spacing:.3f}" for i in range(5)])
            self.setItem(r, 8, QTableWidgetItem(values_text))
            self.setItem(r, 9, QTableWidgetItem(times_text))
        else:  # Major cycle
            self.setItem(r, 8, QTableWidgetItem(f"{value:.4g}"))
            self.setItem(r, 9, QTableWidgetItem(f"{t:.3f}"))