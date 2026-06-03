#!/usr/bin/env python3

# Required libraries:
# pyvisa - connecting via NI VISA architecture
# matplotlib - plotting
# pyqt6 - GUI
# logging - export the log file in case of error

import sys
import HV_GUI as gui

app = gui.QApplication(sys.argv)

window = gui.MainWindow()
window.show()
window.resize(1000, 600)

app.exec()
