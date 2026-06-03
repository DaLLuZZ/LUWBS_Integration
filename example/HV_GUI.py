import matplotlib
import math
import time
import datetime
import json
#import T_client
import threading
import random
import device
#import Read_samples_GUI

from PyQt6 import QtTest
from PyQt6.QtCore import	(	QSize,
								Qt, 
                                QCoreApplication, 
                                QAbstractTableModel, 
                                QTimer,
								QEvent
							)
from PyQt6.QtWidgets import (	QApplication,
								QMainWindow,
								QWidget,
								QCheckBox,
								QComboBox,
								QRadioButton,
								QLabel,
								QLineEdit,
								QTableView,
								QTableWidget,
								QTableWidgetItem,
								QPushButton,
								QGraphicsItem,
								QTextEdit,
								QGridLayout,
								QHBoxLayout,
								QVBoxLayout,
								QFileDialog,
								QMessageBox								
							)
							
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=6, height=5, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(1, 1, 1)
        super(MplCanvas, self).__init__(fig)

class MainWindow(QMainWindow):
	#cc = None
	config_data = None
	B2987 = None

	thread1 = None
	flag_meas_temp = True
	flag_stop = False
	flag_draw = True
	
	meas_status = -1
	current_temperature = 300.0005
	
	current_curve = None
	current_regime = 0 # 0 - Pulse, 1 - Sweep
	current_protection = True
	
	db_sample = None
	db_iv = None
	current_sample = ""
	current_sampleid = -1
	current_area = 0
	current_Ks = 1
	
	t_before_series = 0
	t_before_measurement = 0
	t_before_step = 0
	#t_meas = 0

	def __init__(self):
		try:
			filename = open("config.json", "r")
			self.config_data = json.load(filename)
			filename.close()
			self.config_data["consumer"]["group.id"] += str(random.randint(0, 1000))
			print(self.config_data)
		except Exception as e:
			print(f"JSON import error: {e}")
			self.config_data = {}
		#self.cc = T_client.T_server_consumer(self.config_data)
		#self.cc.time_monitor()
		self.B2987 = device.B2987()
		#self.db_sample = Read_samples_GUI.samples(self.config_data)
		#self.db_sample.read_samples_from_db()
		
		self.arr_V = []
		self.arr_I = []
		self.arr_I_for_draw = []
		self.regimes = ["Pulse", "Sweep", "Double sweep"]
		self.lines_array = []
		
		super(MainWindow, self).__init__()
		self.setWindowTitle("High voltage IV")
		self.setMinimumSize(QSize(800, 500))

		layout_graph = QGridLayout()
		layout_param = QVBoxLayout()
		layout_param_temp = QGridLayout()
		layout_param_chan = QGridLayout()
		layout_param_step = QGridLayout()
		layout_param_results = QVBoxLayout()
		layout_save = QGridLayout()
		layout = QGridLayout()
		
		# ----------------- layout graph -----------------------

		self.canvas = MplCanvas(self, width=6, height=5, dpi=100)
		self.toolbar = NavigationToolbar(self.canvas, self)
		self.IV_list = QTableWidget(0, 2)
		self.IV_list.cellClicked.connect(self.table_clicked)

		# grig format: (name, row, column, rowspan, columnspan)
		layout_graph.addWidget(self.IV_list, 0, 0, 2, 1)
		layout_graph.addWidget(self.toolbar, 0, 1, 1, 1)
		layout_graph.addWidget(self.canvas, 1, 1, 1, 1)
		
		# ----------------- layout param -----------------------
		## ---------------- param temp -------------------------

		label_31_widget = QLabel("T, K")
		self.label_32_widget = QLabel("T_client status")
		self.check_21_widget = QCheckBox("Auto measure") # Measure temperature continiously
		self.check_21_widget.setChecked(False)
		self.check_21_widget.stateChanged.connect(self.temp_auto_measure_changed)
		self.text_31_widget = QLineEdit("300.0001") # Current temperature

		# grig format: (name, row, column, rowspan, columnspan)
		layout_param_temp.addWidget(label_31_widget, 0, 0)
		layout_param_temp.addWidget(self.text_31_widget, 0, 1)
		layout_param_temp.addWidget(self.check_21_widget, 0, 2)
		layout_param_temp.addWidget(self.label_32_widget, 0, 3)
		
		## ---------------- param chan -------------------------

		label_03_widget = QLabel("Regime: ")
		label_04_widget = QLabel("t hold\nbefore\npulse")
		label_05_widget = QLabel("t wait\nbefore\nmeasure")
		label_06_widget = QLabel("t before\nnext\nmeasure")
		
		combo_1_widget = QComboBox(self)
		combo_1_widget.addItems(self.regimes)
		combo_1_widget.currentIndexChanged.connect(self.combo_sweep_pulse_changed)

		self.text_04_widget = QLineEdit("100") # t hold before pulse/sweep
		self.text_05_widget = QLineEdit("100") # t hold before measurement
		self.text_06_widget = QLineEdit("100") # t hold after measurement and before nest step
		
		check_02_widget = QCheckBox("Add internal protection resistor (20 MOhm)")
		check_02_widget.stateChanged.connect(self.check_protection_changed)
		
		# grig format: (name, row, column, rowspan, columnspan)
		layout_param_chan.addWidget(check_02_widget, 3, 1, 1, 3)
		layout_param_chan.addWidget(label_03_widget, 4, 1, 1, 1)
		layout_param_chan.addWidget(combo_1_widget, 4, 2, 1, 1)
		layout_param_chan.addWidget(label_04_widget, 5, 1, 1, 1)
		layout_param_chan.addWidget(label_05_widget, 5, 2, 1, 1)
		layout_param_chan.addWidget(label_06_widget, 5, 3, 1, 1)
		layout_param_chan.addWidget(self.text_04_widget, 6, 1, 1, 1)
		layout_param_chan.addWidget(self.text_05_widget, 6, 2, 1, 1)
		layout_param_chan.addWidget(self.text_06_widget, 6, 3, 1, 1)

		## ---------------- param step -------------------------

		label_11_widget = QLabel("V (I) start, V (A)")
		label_12_widget = QLabel("V (I) end, V (A)")
		label_13_widget = QLabel("V (I) step, V (A)")
		label_14_widget = QLabel("Averaging, PLC")

		self.text_11_widget = QLineEdit("0") # Vstart, V
		self.text_12_widget = QLineEdit("1") # Vend, V
		self.text_13_widget = QLineEdit("0.1") # Vstep, V
		self.text_14_widget = QLineEdit("2") # Averaging, PLC
		
		# grig format: (name, row, column, rowspan, columnspan)
		layout_param_step.addWidget(label_11_widget, 0, 0)
		layout_param_step.addWidget(self.text_11_widget, 1, 0)
		layout_param_step.addWidget(label_12_widget, 0, 1)
		layout_param_step.addWidget(self.text_12_widget, 1, 1)
		layout_param_step.addWidget(label_13_widget, 0, 2)
		layout_param_step.addWidget(self.text_13_widget, 1, 2)
		layout_param_step.addWidget(label_14_widget, 3, 0, 1, 2)
		layout_param_step.addWidget(self.text_14_widget, 3, 2, 1, 1)
		
		## ---------------- param results ----------------------

		label_21_widget = QLabel("Results:")

		self.result_names = QLineEdit()
		self.result_table = QTextEdit()

		layout_param_results.addWidget(label_21_widget)
		layout_param_results.addWidget(self.result_names)
		layout_param_results.addWidget(self.result_table)

		# ----------------- layout save -----------------------

		self.label_22_widget = QLabel("Status")
		self.label_23_widget = QLabel("") # Sample name
		
		self.text_21_widget = QLineEdit("Comment") # Comment
		#self.text_22_widget = QLineEdit("Z:/Data/Meas/IV/") # Path to save
		self.text_22_widget = QLineEdit("Data/Meas/IV/") # Path to save

		self.button_start_widget = QPushButton("Start")
		self.button_start_widget.clicked.connect(self.start_clicked)
		self.button_stop_widget = QPushButton("Stop")
		self.button_stop_widget.clicked.connect(self.stop_clicked)
		button_clear_widget = QPushButton("Clear")
		button_clear_widget.clicked.connect(self.clear_graph)
		button_save_widget = QPushButton("Save as file")
		button_save_widget.clicked.connect(self.save_clicked)
		button_select_sample_widget = QPushButton("Select sample")
		#button_select_sample_widget.clicked.connect(self.select_sample_clicked)
		button_save_to_db_widget = QPushButton("Prepare export file")
		#button_save_to_db_widget.clicked.connect(self.prepare_dbexport)
		button_load_from_db_widget = QPushButton("Load from DB")
		#button_load_from_db_widget.clicked.connect(self.load_curve_from_database)
		button_load_from_file_widget = QPushButton("Load from file")
		#button_load_from_file_widget.clicked.connect(self.load_curve_from_file_clicked)
		button_exit_widget = QPushButton("Exit")
		button_exit_widget.clicked.connect(self.exit_clicked)

		# grig format: (name, row, column, rowspan, columnspan)
		layout_save.addWidget(self.text_21_widget, 0, 0, 1, 5)
		layout_save.addWidget(self.text_22_widget, 1, 0, 1, 5)
		layout_save.addWidget(self.button_start_widget, 2, 0)
		layout_save.addWidget(self.button_stop_widget, 2, 1)
		layout_save.addWidget(button_clear_widget, 2, 2)
		layout_save.addWidget(button_save_widget, 2, 3)
		layout_save.addWidget(button_exit_widget, 2, 4)
		layout_save.addWidget(button_select_sample_widget, 3, 0)
		layout_save.addWidget(self.label_23_widget, 3, 1)
		layout_save.addWidget(button_save_to_db_widget, 3, 2)
		layout_save.addWidget(button_load_from_db_widget, 3, 3)
		layout_save.addWidget(button_load_from_file_widget, 3, 4)
		layout_save.addWidget(self.label_22_widget, 4, 0, 1, 5)
		
		button_select_sample_widget.setDisabled(True)
		button_save_to_db_widget.setDisabled(True)
		button_load_from_db_widget.setDisabled(True)
		button_load_from_file_widget.setDisabled(True)

		# ---------------- all layouts ------------------------------

		layout_param.addLayout(layout_param_temp)
		layout_param.addLayout(layout_param_chan)
		layout_param.addLayout(layout_param_step)
		layout_param.addLayout(layout_param_results)
	
		layout.addLayout(layout_graph, 0, 0)
		layout.addLayout(layout_param, 0, 1)
		layout.addLayout(layout_save, 1, 0, 1, 2)

		widget = QWidget()
		widget.setLayout(layout)

		self.setCentralWidget(widget)
		
		# ---------------- fill values from json --------------------

		try:
			self.check_21_widget.setChecked(bool(self.config_data["saved_parameters"]["flag_temperature_auto_measure"]))
			check_02_widget.setChecked(bool(self.config_data["saved_parameters"]["flag_protection_resistor"]))
			self.text_11_widget.setText(self.config_data["saved_parameters"]["v_start"])
			self.text_12_widget.setText(self.config_data["saved_parameters"]["v_end"])
			self.text_13_widget.setText(self.config_data["saved_parameters"]["v_step"])
			self.text_14_widget.setText(self.config_data["saved_parameters"]["averaging"])
			self.text_04_widget.setText(self.config_data["saved_parameters"]["t_step"])
			self.text_05_widget.setText(self.config_data["saved_parameters"]["t_hold"])
			self.text_06_widget.setText(self.config_data["saved_parameters"]["t_next"])
			self.text_22_widget.setText(self.config_data["saved_parameters"]["file_save_folder"])
		except Exception as e:
			print(str(e))
			self.set_status("JSON import error: saved_parameters")

		self.set_status(self.B2987.idn().replace("\n", " "))
		
	# ===== Buttons and connections ======================================================

	def temp_auto_measure_changed(self, state):
		print("Auto temerature measurement status changed to " + str(state))
		self.flag_meas_temp = bool(state)
		#if (self.flag_meas_temp):
		#	self.init_temperature()
		#else:
		#	self.destroy_temperature()
		self.set_status("Auto temerature measurement status is " + str(self.flag_meas_temp))

	def check_protection_changed(self, state):
		state = bool(state)
		print("check_protection_changed", state)
		self.current_protection = state
		self.B2987.add_r_lim(state)

	def combo_sweep_pulse_changed(self, index):
		print("combo_sweep_pulse_changed", index)
		self.current_regime = index

	def start_clicked(self):
		self.flag_stop = False

		self.result_names.clear()
		self.result_table.clear()
		self.arr_V.clear()
		self.arr_I.clear()
		self.arr_I_for_draw.clear()
		
		if not (self.current_curve is None):
			self.current_curve.set_xdata(self.arr_V)
			self.current_curve.set_ydata(self.arr_I_for_draw)

		self.result_names.setText("Voltage, V\tCurrent, A\tRdiff, Ohm")
		
		try:
			self.v_start = float(self.text_11_widget.text())
			self.v_end = float(self.text_12_widget.text())
			self.v_step = float(self.text_13_widget.text())
			self.t_before_series = float(self.text_04_widget.text())/1000
			self.t_before_measurement = float(self.text_05_widget.text())/1000
			self.t_before_step = float(self.text_06_widget.text())/1000
			self.current_PLC = float(self.text_14_widget.text())
		except Exception as e:
			print("Voltage error: ", e)
			return -1
		
		temp_V_array = []
		temp_I_array = []
		for i in range(int(self.v_start), int(self.v_end)):
			temp_V_array.append(i)
			temp_I_array.append(i/2e7)
		temp_curve, = self.canvas.axes.plot(temp_V_array, temp_I_array, color = 'tab:gray', linewidth = "1")
		
		if (abs(self.v_start) <= 20) and (abs(self.v_end) <= 20):
			self.B2987.set_voltage_range(20)
			print("Range: +-20 V")
		else:
			if (self.v_start < -1) and (self.v_end > 1):
				print("Voltage range error")
				return -2
			if (self.v_end < -1) and (self.v_start > 1):
				print("Voltage range error")
				return -3
			if (abs(self.v_step) > abs(self.v_start - self.v_end)):
				print("Voltage step error")
				return -4
			if (self.v_start < -20) or (self.v_end < -20):
				self.B2987.set_voltage_range(-1000)
				print("Range: -1000 V")
			if (self.v_start > 20) or (self.v_end > 20):
				self.B2987.set_voltage_range(1000)
				print("Range: +1000 V")
			
		self.B2987.set_mode_current()
		self.B2987.set_aperture_PLC(self.current_PLC)
		self.B2987.turn_input(True)
		self.wait_for_t(0.1)

		self.meas_status = 0
		self.start_measure()
		
		self.set_status("Single channel measure done")
		self.update_json_parameters()
		return self.meas_status
	
	def stop_clicked(self):
		self.flag_stop = True
		self.B2987.abort()
		self.B2987.turn_output(False)
		self.B2987.turn_input(False)
		self.set_status("Stop")
		self.meas_status = 2

	def save_clicked(self):
		if (self.meas_status>0):
			self.save_to_file()
		else:
			print("No data to save or data was corrupted")
		
	def exit_clicked(self):
		self.flag_meas_temp = False
		if not self.thread1 is None:
			self.thread1.join()
			self.thread1 = None
		#self.cc.close()
		self.B2987.abort()
		self.B2987.turn_output(False)
		self.B2987.turn_input(False)
		self.B2987.close_connection()
		QApplication.exit()

	# ===== Measuring functions ==========================================================

	def add_to_table(self, target_arr):
		target_string = ""
		for i in target_arr:
			target_string += '{:.4e}'.format(i) + "\t"
		self.result_table.append(target_string)
		
	def start_measure(self):
		current_value = 0
		
		self.arr_V.clear()
		self.arr_I.clear()
		self.arr_I_for_draw.clear()
		
		if (self.v_start == self.v_end):
			print("single point")
			voltage = self.v_start
			try:
				measured_current = self.measure_single_point_pulse(voltage)
			except Exception as e:
				print("measuring error: {0:s}".format(str(e)))
				return 0b000100
			self.arr_V.append(voltage)
			self.arr_I.append(measured_current)
			self.arr_I_for_draw.append(abs(measured_current)+1e-14)
			if abs(measured_current) > 1e-14:
				Rdiff = voltage / measured_current
			else:
				Rdiff = 0
			self.add_to_table([voltage, measured_current, Rdiff])
			self.stop_clicked()
			self.meas_status = 1
			self.set_status("Single point measurement complete")
			return 0b000011
		else:
			print("Single branch")
			self.prepare_canvas(self.v_start, self.v_end)
			if (self.v_end > self.v_start):
				value_step = abs(self.v_step)
			else:
				value_step = -abs(self.v_step)
			num = int((self.v_end - self.v_start)/value_step) + 1
			
			if self.current_regime == 0: # pulse from 0 to voltage
				self.B2987.set_voltage(self.v_start)
				self.wait_for_t(self.t_before_series)
				for i in range(num):
					if self.flag_stop:
						self.set_status("Measurement aborted")
						self.meas_status = 2
						self.stop_clicked()
						break
					voltage = self.v_start + value_step*i
					print(voltage)
					flag_long = False
					if abs(voltage) < 1:
						flag_long = True
					if abs(self.v_start + value_step*(i-1)) < 1:
						flag_long = True
					try:
						measured_current = self.measure_single_point_pulse(voltage, long_sleep = flag_long)
					except Exception as e:
						print("measuring error: {0:s}".format(str(e)))
						return 0b0001000
					self.arr_V.append(voltage)
					self.arr_I.append(measured_current)
					self.arr_I_for_draw.append(abs(measured_current)+1e-14)
					try:
						ll = len(self.arr_V)
						Rdiff = (self.arr_V[ll-1] - self.arr_V[ll-2])/(self.arr_I[ll-1] - self.arr_I[ll-2])
					except Exception as e:
						Rdiff = 0
					self.add_to_table([voltage, measured_current, Rdiff])
					self.redraw()
					self.wait_for_t(self.t_before_step)
					
			if self.current_regime == 1: # sweep from previous to next voltage
				self.B2987.set_voltage(self.v_start)
				self.B2987.turn_output(True)
				self.wait_for_t(self.t_before_series)
				for i in range(num):
					if self.flag_stop:
						self.set_status("Measurement aborted")
						self.meas_status = 2
						self.stop_clicked()
						break
					voltage = self.v_start + value_step*i
					print(voltage)
					flag_long = False
					if abs(voltage) < 1:
						flag_long = True
					if abs(self.v_start + value_step*(i-1)) < 1:
						flag_long = True
					try:
						measured_current = self.measure_single_point_sweep(voltage, long_sleep = flag_long)
					except Exception as e:
						print("measuring error: {0:s}".format(str(e)))
						return 0b0010000
					self.arr_V.append(voltage)
					self.arr_I.append(measured_current)
					self.arr_I_for_draw.append(abs(measured_current)+1e-14)
					try:
						ll = len(self.arr_V)
						Rdiff = (self.arr_V[ll-1] - self.arr_V[ll-2])/(self.arr_I[ll-1] - self.arr_I[ll-2])
					except Exception as e:
						Rdiff = 0
					self.add_to_table([voltage, measured_current, Rdiff])
					self.redraw()
					self.wait_for_t(self.t_before_step)
				self.B2987.turn_output(False)
				
			if self.current_regime == 2: # double sweep: from previous to next voltage and back
				self.B2987.set_voltage(self.v_start)
				self.B2987.turn_output(True)
				self.wait_for_t(self.t_before_series)
				for i in range(num):
					if self.flag_stop:
						self.set_status("Measurement aborted")
						self.meas_status = 2
						self.stop_clicked()
						break
					voltage = self.v_start + value_step*i
					print(voltage)
					flag_long = False
					if abs(voltage) < 1:
						flag_long = True
					if abs(self.v_start + value_step*(i-1)) < 1:
						flag_long = True
					try:
						measured_current = self.measure_single_point_sweep(voltage, long_sleep = flag_long)
					except Exception as e:
						print("measuring error: {0:s}".format(str(e)))
						return 0b0100000
					self.arr_V.append(voltage)
					self.arr_I.append(measured_current)
					self.arr_I_for_draw.append(abs(measured_current)+1e-14)
					try:
						ll = len(self.arr_V)
						Rdiff = (self.arr_V[ll-1] - self.arr_V[ll-2])/(self.arr_I[ll-1] - self.arr_I[ll-2])
					except Exception as e:
						Rdiff = 0
					self.add_to_table([voltage, measured_current, Rdiff])
					self.redraw()
					self.wait_for_t(self.t_before_step)
				self.wait_for_t(self.t_before_series)
				for i in range(num):
					if self.flag_stop:
						self.set_status("Measurement aborted")
						self.meas_status = 2
						self.stop_clicked()
						break
					voltage = self.v_end - value_step*i
					print(voltage)
					flag_long = False
					if abs(voltage) < 1:
						flag_long = True
					if abs(self.v_end - value_step*(i-1)) < 1:
						flag_long = True
					measured_current = self.measure_single_point_sweep(voltage, long_sleep = flag_long)
					self.arr_V.append(voltage)
					self.arr_I.append(measured_current)
					self.arr_I_for_draw.append(abs(measured_current)+1e-14)
					try:
						ll = len(self.arr_V)
						Rdiff = (self.arr_V[ll-1] - self.arr_V[ll-2])/(self.arr_I[ll-1] - self.arr_I[ll-2])
					except Exception as e:
						Rdiff = 0
					self.add_to_table([voltage, measured_current, Rdiff])
					self.redraw()
					self.wait_for_t(self.t_before_step)
				self.B2987.turn_output(False)
				
			self.meas_status = 1
			self.set_status("Single branch measurement complete")
			return 0b001000

	def measure_single_point_pulse(self, target_voltage, long_sleep = False):
		self.B2987.set_voltage(target_voltage)
		self.B2987.turn_output(True)
		self.wait_for_t(self.t_before_measurement)
		try:
			self.B2987.shot_measure_current()
			self.wait_for_t(3)
			#if (long_sleep):
			#	self.wait_for_t(5)
			self.wait_for_t(self.current_PLC * 0.03)
			measured_current = float(self.B2987.read())
		except Exception as e:
			print("Measuring error:", e)
			self.set_status("Measuring error")
			measured_current = 0
		finally:
			self.B2987.turn_output(False)
			return measured_current
		
	def measure_single_point_sweep(self, target_voltage, long_sleep = False):
		self.B2987.set_voltage(target_voltage)
		self.wait_for_t(self.t_before_measurement)
		try:
			self.B2987.shot_measure_current()
			if (long_sleep):
				self.wait_for_t(5)
			self.wait_for_t(self.current_PLC * 0.03)
			measured_current = float(self.B2987.read())
		except Exception as e:
			print("Measuring error:", e)
			self.set_status("Measuring error")
			measured_current = 0
		finally:
			return measured_current

	def prepare_canvas(self, V_min, V_max):
		self.flag_draw = True
		#self.canvas.axes.cla()
		if (V_min == V_max):
			print("graph error")
			self.flag_draw = False
		self.canvas.axes.set_xlim(min(V_min, V_max), max(V_min, V_max))
		self.canvas.axes.set_ylim(1e-11, 1e-3)
		self.canvas.axes.set_yscale('log')
		self.canvas.axes.set_xlabel('Voltage, V')
		self.canvas.axes.set_ylabel('Current, A')
		self.current_curve, = self.canvas.axes.plot(self.arr_V, self.arr_I_for_draw, 'r', linewidth = "3")
		self.canvas.draw()

	def redraw(self):
		if not self.flag_draw:
			print("Flag_draw is False")
			return 0
		
		Vmin = float(self.text_11_widget.text())
		Vmax = float(self.text_12_widget.text())
		if Vmin > Vmax:
			V_temp = Vmin
			Vmin = Vmax
			Vmax = V_temp
		Vmin = Vmin * 0.95
		Vmax = Vmax * 1.05

		if (self.meas_status >= 0):
			I_max = max(self.arr_I_for_draw)
			I_min = min(self.arr_I_for_draw)
		else:
			I_max = 1e-9
			I_min = 1e-11
			
		if len(self.lines_array) > 0:
			for i in self.lines_array:
				if i.min_V < Vmin:
					Vmin = i.min_V*0.95
				if i.max_V > Vmax:
					Vmax = i.max_V*1.05
				if i.min_I < I_min:
					I_min = i.min_I*0.95
				if i.max_V > I_max:
					I_max = i.max_V*1.05
		I_max = math.pow(10, math.ceil(math.log10(I_max)))
		I_min = math.pow(10, math.floor(math.log10(I_min)))
		self.canvas.axes.set_ylim(I_min, I_max)
		
		if (self.meas_status >= 0):
			self.current_curve.set_xdata(self.arr_V)
			self.current_curve.set_ydata(self.arr_I_for_draw)
		
		self.canvas.draw()
		self.toolbar.update()

	def save_to_file(self):
		filter_dict = {
			'Plain text: *.txt (*.txt)': '.txt',
			'CSV file: *.csv (*.csv)': '.csv',
			"All files (*)": ""
			}
		filter_str = ""
		target_directory = self.text_22_widget.text()
		for i in filter_dict.keys():
			filter_str += i
			filter_str += ";;"
		fd = QFileDialog.getSaveFileName(
			parent = self,
			caption = "save to file",
			#directory = ".",
			directory = target_directory,
			filter = filter_str)
		new_fd = fd
		if not (fd[0] == ""):
			if not (fd[0].endswith(filter_dict[fd[1]])):
				new_fd = ([fd[0] + str(filter_dict[fd[1]]), fd[1]])
			print("Filename:", new_fd[0])
		filename = open(new_fd[0], "w+")
		filename.write(self.text_21_widget.text()+"\n")
		filename.write("Temperature: " + self.text_31_widget.text()+"\n")

		filename.write("Voltage (V), \t Current (A)\n")
		for i in range(len(self.arr_V)):
			filename.write(str(float(self.arr_V[i])) + ", \t" + str(float(self.arr_I[i])) + "\n")

		filename.close()
		self.set_status("Data saved")

	def set_status(self, target_text):
		self.label_22_widget.setText(str(target_text))

	def wait_for_t(self, target_time):
		QtTest.QTest.qWait(target_time*1000)

	def closeEvent(self, event):
		self.exit_clicked()

	# ===== Threads ======================================================================

	#def init_temperature(self):
	#	self.thread1 = threading.Thread(target = self.thread_temperature_measurement, args=())
	#	self.thread1.start()
	#	print("init_temperature proc")

	#def thread_temperature_measurement(self):
	#	while self.flag_meas_temp:
	#		QtTest.QTest.qWait(1000)
	#		if self.check_21_widget.isChecked():
	#			if self.cc.data_obt_flag():
	#				self.current_temperature = self.cc.get_avg_T(3)
	#				self.text_31_widget.setText('{:.2f}'.format(self.current_temperature))
	#				self.label_32_widget.setText("T monitoring")
	#			else:
	#				self.text_31_widget.setText("300.0002")
	#				self.label_32_widget.setText("No data")
					
	# ===== Database ======================================================================
					
	def select_sample_clicked(self):
		print("sample selection")
		self.db_sample.show_sample_window()
		print("Sample window showed")
		while(self.db_sample.get_status() < 0):
			self.wait_for_t(0.5)
		print("Sample selected")

		self.current_sample = self.db_sample.get_current_sample()
		self.current_sampleid = self.db_sample.get_current_sampleid()
		self.current_area = self.db_sample.get_current_area()
		self.current_Ks = self.db_sample.get_current_Ks()
		if (self.current_sampleid > 0):
			print("(ID {0:d}) Sample is {1:s} (Area = {2:f}, Ks = {3:f})".format(self.current_sampleid, self.current_sample, self.current_area, self.current_Ks))
			self.label_23_widget.setText(self.current_sample)
		else:
			print("Sample not choosed")
			self.label_23_widget.setText("")
			
	def prepare_dbexport(self):
		if (self.meas_status < 1):
			print("Current status is {0:d}".format(self.meas_status))
			self.set_status("No data to export or data was corrupted")
			return -2
		if (self.current_sampleid < 1):
			self.set_status("Choose the sample")
			return -1
		string_V = ""
		string_I = ""
		string_V2 = ""
		string_I2 = ""
		for i in range(len(self.arr_V)):
			string_V += "{0:.6g}\n".format(self.arr_V[i]).replace(",", ".")
			string_I += "{0:.6g}\n".format(self.arr_I[i]).replace(",", ".")
			if self.flag_meas_state == 0b11:
				string_V2 += "{0:.6g}\n".format(self.arr_V_2[i]).replace(",", ".")
				string_I2 += "{0:.6g}\n".format(self.arr_I_2[i]).replace(",", ".")
		string_V += "\n"
		string_I += "\n"
		string_V = string_V.replace("\n\n", "")
		string_I = string_I.replace("\n\n", "")
		if self.flag_meas_state == 0b11:
			string_V2 += "\n"
			string_I2 += "\n"
			string_V2 = string_V2.replace("\n\n", "")
			string_I2 = string_I2.replace("\n\n", "")
		
		measure_time = int(time.time())
		temp_comment = self.text_21_widget.text()
		for i in [";", "\\", "\"", "&", "drop", "DROP", "'", "%"]:
			temp_comment = temp_comment.replace(i, "*")
		vmin = float(self.text_11_widget.text())
		vmax = float(self.text_12_widget.text())
		vstep = float(self.text_13_widget.text())
		n_points = int((abs(vmax-vmin))/abs(vstep))+1
		if (self.flag_begin_from_zero):
			n_points += 1

		value_1 = self.text_01_widget.text()
		if (self.flag_V_I_state & 0b01 == 0b01):
			value_1 += "A"
		else:
			value_1 += "V"
		value_2 = self.text_03_widget.text()
		if (self.flag_V_I_state & 0b10 == 0b10):
			value_2 += "A"
		else:
			value_2 += "V"
		if (self.flag_meas_state == 0b11):
			bothch = "true"
		else:
			bothch = "false"

		exportstring = "{\n"
		exportstring += "\t\"SampleName\": \"{0:s}\",\n".format(self.current_sample)
		exportstring += "\t\"DateMeas\": \"{0:s}\",\n".format(datetime.datetime.fromtimestamp(measure_time).isoformat())
		exportstring += "\t\"Ks\": {0:.1f},\n".format(self.current_Ks)
		exportstring += "\t\"Npoints\": {0:d},\n".format(n_points)
		exportstring += "\t\"T\": {0:.3f},\n".format(float(self.current_temperature))
		exportstring += "\t\"td\": {0:.3f},\n".format(float(self.text_15_widget.text()))
		exportstring += "\t\"th\": {0:.3f},\n".format(float(self.text_16_widget.text()))
		exportstring += "\t\"Vmin\": {0:.3f},\n".format(vmin)
		exportstring += "\t\"Vmax\": {0:.3f},\n".format(vmax)
		exportstring += "\t\"Vstep\": {0:.3f},\n".format(vstep)
		exportstring += "\t\"DateModif\": \"{0:s}\",\n".format(datetime.datetime.fromtimestamp(measure_time).isoformat())
		exportstring += "\t\"V\": \"{0:s}\",\n".format(string_V)
		exportstring += "\t\"I\": \"{0:s}\",\n".format(string_I)
		exportstring += "\t\"Snx\": {0:.6f},\n".format(self.current_area)
		exportstring += "\t\"Remark\": \"{0:s}\",\n".format(temp_comment)
		exportstring += "\t\"Voltage1\": \"{0:s}\",\n".format(value_1)
		exportstring += "\t\"Voltage2\": \"{0:s}\",\n".format(value_2)
		exportstring += "\t\"Voltage3\": \"\",\n"
		exportstring += "\t\"SMU_meas\": {0:d},\n".format(self.flag_meas_state)
		exportstring += "\t\"SMU_sweep\": {0:d},\n".format(self.flag_sweep)
		exportstring += "\t\"PLC\": true,\n"
		exportstring += "\t\"N_PLC\": {0:d},\n".format(int(self.text_14_widget.text()))
		exportstring += "\t\"device\": \"B2987\",\n"
		exportstring += "\t\"V_Ch2\": \"{0:s}\",\n".format(string_V2)
		exportstring += "\t\"I_Ch2\": \"{0:s}\",\n".format(string_I2)
		exportstring += "\t\"BothCh\": {0:s},\n".format(bothch)
		exportstring += "}"
		
		if ("drop" in exportstring.lower()):
			self.set_status("Saving error: critical drop database error")
			return -3
			
		exportfilename = self.config_data["database"]["DBexportfolder"]
		exportfilename += "IV_" + self.current_sample
		exportfilename += datetime.datetime.fromtimestamp(measure_time).strftime('_%Y%m%d_%H%M%S.dbexport')

		try:
			db_export_file = open(exportfilename, "w+")
			db_export_file.write(exportstring)
			db_export_file.close()
			print("File saved: " + exportfilename)
			self.set_status("Data saved to {0:s}".format(exportfilename))
			if self.flag_meas_state < 0b11:
				self.load_curve_from_file(exportfilename)
			return exportfilename
		except Exception as e:
			print(str(e))
			self.set_status("Export error")
			return None

	def clear_graph(self):
		self.canvas.axes.cla()
		print("\"Clear\" button was pressed")
		for i in self.lines_array:
			i.close()
		self.lines_array.clear()
		self.IV_list.clear()
		for _ in range(self.IV_list.rowCount()):
			self.IV_list.removeRow(0)
		self.canvas.draw()

	def load_curve_from_database(self):
		print("Loading IV from database. Curve selection")
		self.db_sample.show_sample_window()
		print("Curve window showed")
		while (self.db_sample.get_status() < 0):
			self.wait_for_t(0.5)
		print("Curve window closed")
		if not (self.db_sample.get_flag_selected()):
			print("IV not choosen")
			return -1
		
		new_id = self.db_sample.get_current_iv_id()
		if new_id < 0:
			print("no DB entry found")
			return -1
		temp_array = self.db_sample.load_IV_from_DB(new_id)
		V_array = []
		I_array = []
		for i in temp_array[0][0].split('\n'):
			V_array.append(float(i))
		for i in temp_array[0][1].split('\n'):
			I_array.append(float(i))
		#print(F_array[0], I_array[0])
		line_name = self.db_sample.get_current_iv_name()
		cc = IV_curve(line_name)
		cc.fill_values(V_array, I_array)
		cc.curve, = self.canvas.axes.plot(cc.V_array, cc.I_array, color = cc.generate_color(), linewidth = "1")
		
		temp_num = self.IV_list.rowCount()
		self.IV_list.insertRow(temp_num)
		self.IV_list.setCellWidget(temp_num, 0, cc.visible_checkbox)
		cc.visible_checkbox.clicked.connect(self.redraw)
		self.IV_list.setCellWidget(temp_num, 1, QLabel(self.db_sample.get_current_iv_remark()))

		self.lines_array.append(cc)
		self.redraw()
		
	def load_curve_from_file_clicked(self):
		self.load_curve_from_file()

	def load_curve_from_file(self, target_filename = None):
		target_directory = "Z:\DATA\Meas\DBexportfolder"
		filter_dict = {
			'DB export file: *.dbexport (*.dbexport)': '.dbexport'
			}
		filter_str = ""
		for i in filter_dict.keys():
			filter_str += i
			filter_str += ";;"
		print("Loading IV from file. Curve selection")
		if (target_filename is None):
			fd = QFileDialog.getOpenFileName(
				parent = self,
				caption = "save to file",
				directory = target_directory,
				filter = filter_str)
			if (fd[0] == ""):
				print("No file selected")
				return -2
			target_filename = fd[0]
		if not (target_filename.endswith(".dbexport")):
			print("File import error: not DBexport file")
			return -1
		print("Filename: ", target_filename)
		try:
			filename = open(target_filename, "r")
			temp_file_strings = ""
			for i in filename.readlines():
				temp_file_strings += i
			filename.close()
			read_samplename = temp_file_strings.split("\"SampleName\": \"")[1].split("\",")[0]
			read_remark = temp_file_strings.split("\"Remark\": \"")[1].split("\",")[0]
			read_v_string = temp_file_strings.split("\"V\": \"")[1].split("\",")[0]
			read_i_string = temp_file_strings.split("\"I\": \"")[1].split("\",")[0]
			#print("file readed")
			#print(read_samplename)
			#print(read_remark)
			#print(read_f_string)
			#print(read_c_string)
			float_v_array = []
			float_i_array = []
			for i in read_v_string.split("\n"):
				if len(i) > 0:
					float_v_array.append(float(i))
			for i in read_i_string.split("\n"):
				if len(i) > 0:
					float_i_array.append(float(i))
				
			cc = IV_curve(read_samplename)
			cc.fill_values(float_v_array, float_i_array)
			cc.curve, = self.canvas.axes.plot(cc.V_array, cc.I_array, color = cc.generate_color(), linewidth = "1")
			
			temp_num = self.IV_list.rowCount()
			self.IV_list.insertRow(temp_num)
			self.IV_list.setCellWidget(temp_num, 0, cc.visible_checkbox)
			cc.visible_checkbox.clicked.connect(self.redraw)
			self.IV_list.setCellWidget(temp_num, 1, QLabel(read_remark))

			self.lines_array.append(cc)
			self.redraw()
		except Exception as e:
			print(e)

	def table_clicked(self, target_row, target_column):
		for i in range(len(self.lines_array)):
			self.lines_array[i].flag_selected = (i == target_row)
			self.lines_array[i].update_thickness()
		self.redraw()
		
	def update_json_parameters(self):
		new_config_data = self.config_data
		new_config_data["saved_parameters"]["flag_temperature_auto_measure"] = self.check_21_widget.isChecked()
		new_config_data["saved_parameters"]["flag_protection_resistor"] = self.current_protection
		new_config_data["saved_parameters"]["v_start"] = self.text_11_widget.text()
		new_config_data["saved_parameters"]["v_end"] = self.text_12_widget.text()
		new_config_data["saved_parameters"]["v_step"] = self.text_13_widget.text()
		new_config_data["saved_parameters"]["averaging"] = self.text_14_widget.text()
		new_config_data["saved_parameters"]["t_step"] = self.text_04_widget.text()
		new_config_data["saved_parameters"]["t_hold"] = self.text_05_widget.text()
		new_config_data["saved_parameters"]["t_next"] = self.text_06_widget.text()
		new_config_data["saved_parameters"]["file_save_folder"] = self.text_22_widget.text()
		new_config_data["consumer"]["group.id"] = "HV_Keysight_"
		
		try:
			filename = open("config.json", "w")
			json.dump(new_config_data, filename, indent=2)
			filename.close()
			return 1
		except Exception as e:
			print(e)
			self.set_status("Save JSON error: saved_parameters")
			return 0
		
class IV_curve():
	index = -1
	min_V = 0
	max_V = 0
	min_I = 0
	max_I = 0
	
	flag_selected = False
	flag_visible = True

	visible_checkbox = None
	curve = None
	curve_name = "Name"

	def __init__(self, target_name = "Name"):
		print("New curve created")
		self.V_array = []	# frequency in Hz
		self.I_array = []	# capacitance in pF
		self.line_color = [0, 0, 0] #R, G, B
		self.generate_color()
		self.curve_name = target_name
		self.visible_checkbox = QCheckBox(self.curve_name)
		self.visible_checkbox.setChecked(True)
		self.visible_checkbox.stateChanged.connect(self.set_visible)
		#self.visible_checkbox.clicked.connect(self.is_clicked)

	def close(self):
		self.V_array = None
		self.I_array = None
		del self.V_array
		del self.I_array

	def set_name(self, target_name):
		self.curve_name = target_name
		self.visible_checkbox.setText(target_name)

	def fill_values(self, target_V_array, target_I_array):
		if not (len(target_I_array) == len(target_V_array)):
			print("Error with the arrays lenght")
			return -1
		if len(target_I_array) < 1:
			print("Array lenght error")
			return -2
		self.V_array = target_V_array[:]
		for i in target_I_array:
			if i == 0:
				self.I_array.append(1e-14)
			else:
				self.I_array.append(abs(i))
		self.min_V = min(self.V_array)
		self.max_V = max(self.V_array)
		self.min_I = min(self.I_array)
		self.max_I = max(self.I_array)
		return len(self.V_array)
	
	def generate_color(self):
		self.line_color = [random.randint(0, 171), random.randint(0, 171), random.randint(0, 171)]
		
	def set_name(self, target_name):
		name = target_name
		
	def set_visible(self, state):
		self.curve.set_visible(state)
		#print(self.curve_name + " stateChanged")
		
	#def is_clicked(self):
		#print(self.curve_name + " clicked")

	def update_thickness(self):
		if (self.flag_selected):
			self.curve.set_linewidth(3)
		else:
			self.curve.set_linewidth(1)
