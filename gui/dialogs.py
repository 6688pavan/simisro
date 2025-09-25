# Small reusable dialogs, e.g., confirm
from PyQt5.QtWidgets import QMessageBox

def confirm_dialog(message):
    return QMessageBox.question(None, "Confirm", message, QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes