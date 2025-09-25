from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QCheckBox
from PyQt5.QtCore import Qt

class ParameterTableWidget(QTableWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setColumnCount(8)
        self.setHorizontalHeaderLabels(["sl.no", "Parameter", "Packet ID", "Offset", "Type", "Enabled", "Instantaneous Value", "Instantaneous Time"])
        self.setSelectionBehavior(QTableWidget.SelectRows)

    def update_table(self, params):
        self.setRowCount(len(params))
        for i, p in enumerate(params):
            self._set_row(i, p)

    def add_row(self, p):
        row = self.rowCount()
        self.setRowCount(row + 1)
        self._set_row(row, p)

    def update_row(self, row, p):
        self._set_row(row, p)

    def _set_row(self, row, p):
        self.setItem(row, 0, QTableWidgetItem(str(p.sl_no)))
        self.setItem(row, 1, QTableWidgetItem(p.name))
        self.setItem(row, 2, QTableWidgetItem(str(p.packet_id)))
        self.setItem(row, 3, QTableWidgetItem(str(p.offset)))
        self.setItem(row, 4, QTableWidgetItem(p.dtype))
        check = QCheckBox()
        check.setChecked(p.enabled)
        check.stateChanged.connect(lambda state, param_name=p.name: self.parent.waveform_plot.toggle_curve(param_name, bool(state)))
        self.setCellWidget(row, 5, check)
        self.setItem(row, 6, QTableWidgetItem("0.0"))
        self.setItem(row, 7, QTableWidgetItem("0.0"))

    def update_instantaneous(self, param_name, value, time):
        for row in range(self.rowCount()):
            if self.item(row, 1).text() == param_name:
                self.item(row, 6).setText(f"{value:.2f}")
                self.item(row, 7).setText(f"{time:.2f}")
                break