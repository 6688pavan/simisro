import sys
import time
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow
from utils.io_helpers import load_parameters_from_file

app = QApplication(sys.argv)
win = MainWindow()
# Load dummy params
params = load_parameters_from_file('dummy_params.csv')
win.parameter_list.parameters = params
win.param_table.update_table(params)

from PyQt5.QtCore import QTimer
# Forward thread logs to stdout for test visibility
def forward_log(msg, level):
	print(f'LOG {level}: {msg}', flush=True)
win.signals.log_message = None

def step1_start():
	print('Starting simulation...', flush=True)
	# Connect thread signals to terminal prints after threads exist
	win.setup_threads()
	win.seeder_thread.signals.log_message.connect(lambda m, l: print(f'SEEDER LOG {l}: {m}', flush=True))
	win.sender_thread.signals.log_message.connect(lambda m, l: print(f'SENDER LOG {l}: {m}', flush=True))
	win.seeder_thread.signals.error.connect(lambda e: print(f'SEEDER ERROR: {e}', flush=True))
	win.sender_thread.signals.error.connect(lambda e: print(f'SENDER ERROR: {e}', flush=True))
	win.start_simulation()

def step2_stop():
	print('Stopping simulation...', flush=True)
	win.stop_simulation()

def step3_restart():
	print('Restarting simulation...', flush=True)
	win.start_simulation()

def step4_final_stop():
	print('Stopping final...', flush=True)
	win.stop_simulation()
	print('Done', flush=True)
	app.quit()

QTimer.singleShot(100, step1_start)       # start after 100ms
QTimer.singleShot(1100, step2_stop)       # stop after 1s
QTimer.singleShot(1600, step3_restart)    # restart after 1.6s
QTimer.singleShot(2600, step4_final_stop) # final stop after ~2.6s

app.exec_()
