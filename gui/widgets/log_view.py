from PyQt5.QtWidgets import QTextEdit, QVBoxLayout, QWidget, QCheckBox, QHBoxLayout

class LogViewWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)
        filter_lay = QHBoxLayout()
        self.info_check = QCheckBox("Info")
        self.info_check.setChecked(True)
        self.warning_check = QCheckBox("Warning")
        self.warning_check.setChecked(True)
        self.error_check = QCheckBox("Error")
        self.error_check.setChecked(True)
        filter_lay.addWidget(self.info_check)
        filter_lay.addWidget(self.warning_check)
        filter_lay.addWidget(self.error_check)
        layout.addLayout(filter_lay)
        # Filters not fully implemented; assume all shown

    def add_log(self, msg, level="INFO"):
        color = {"INFO": "black", "WARNING": "orange", "ERROR": "red"}.get(level, "black")
        self.text_edit.append(f'<font color="{color}">{level}: {msg}</font>')
        self.text_edit.ensureCursorVisible()