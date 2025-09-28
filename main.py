# main.py
import sys
from PyQt5 import QtWidgets
from gui.main_window import MainWindow

def main():
    app = QtWidgets.QApplication(sys.argv)
    
    # Set application-wide grey theme
    app.setStyle('Fusion')  # Use Fusion style for better dark theme support
    
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
