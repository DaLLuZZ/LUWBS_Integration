#import string
import pyvisa
import time
import logging

class scpi_device():
	inst = None
	status = "Idle"
	model_type = "Device"
	device_address = None
	read_termination = None
	
	def __init__(self):
		logging.basicConfig(
			level=logging.WARNING,
			#filename="C:/temp/err_log.txt",
			filename="err_log.txt",
			format = "========== \n%(asctime)s \n%(levelname)s %(message)s",
			force = True)
		
	def connect(self):
		rm = pyvisa.ResourceManager()
		print(rm.list_resources())
		try:
			self.inst = rm.open_resource(self.device_address)
			if not (self.read_termination is None):
				self.inst.read_termination = self.read_termination
			self.status = "Connection to {0:s}".format(self.model_type)
			print(self.inst)
		except Exception as e:
			print("{0:s} import error: {1:s}".format(self.model_type, str(e)))
			self.status = "Connection error"
		finally:
			print(self.status)
		del rm

	def get_status(self):
		return self.status
	
	def write(self, text_to_write):
		self.inst.write(text_to_write)
		return len(text_to_write)

	def read(self):
		try:
			a = self.inst.read()
			return a
		except Exception as e:
			print("{0:s} read error: {1:s}".format(self.model_type, str(e)))
			return None
			
	def query(self, text_to_write):
		try:
			a = self.inst.query(text_to_write)
			return a
		except Exception as e:
			print("{0:s} read error: {1:s}".format(self.model_type, str(e)))
			return None

	def close_connection(self):
		self.inst = None
		print("closed")
	
	def idn(self):
		# Test message, "Who you are?"
		if not (self.inst is None):
			self.inst.write('*IDN?')
			b = self.inst.read()
			print(b)
			return b
		else:
			return "IDN error: self.inst is None"

class B1500():
	inst = None
	status = "Idle"
    
	def __init__(self):
		rm = pyvisa.ResourceManager()
		print(rm.list_resources())
		try:
			self.inst = rm.open_resource('GPIB1::17::INSTR')
			status = "Connection to B1500"
			print(self.inst)
		except Exception as e:
			print("B1500 import error: " + str(e))
			status = "Connection error"
		finally:
			print(status)
		del rm
		logging.basicConfig(
			level=logging.WARNING,
			filename="C:/temp/err_log.txt",
			format = "========== \n%(asctime)s \n%(levelname)s %(message)s",
			force = True)
			
	def write(self, text_to_write):
		self.inst.write(text_to_write)
		b = self.check_err("write")
		if (b != 0):
			return b
		else:
			return len(text_to_write)
			
	def write_without_err_check(self, text_to_write):
		self.inst.write(text_to_write)

	def read(self):
		a = self.inst.read()
		b = self.check_err("write")
		if (b != 0):
			return b
		else:
			return a
			
	def query(self, text_to_write):
		a = self.inst.query(text_to_write)
		b = self.check_err("write")
		if (b != 0):
			return b
		else:
			return a

	def close_connection(self):
		self.inst = None
		print("closed")
	
	def idn(self):
		# Test message, "Who you are?"
		if not (self.inst is None):
			self.inst.write('*IDN?')
			b = self.inst.read()
			print(b)
			return b
		else:
			return "IDN error: self.inst is None"

	def cl(self):
		# Turn OFF all channels
		self.inst.write('CL')

	def cn(self):
		# Turn ON all CMS channels
		self.inst.write('CN 1, 3, 5, 6, 7')

	def cn_HPSMU(self):
		# Turn on HPSMU channel (1, 3)
		self.inst.write('CN 1, 3')

	def cn_MPSMU(self):
		# Turn on MPSMU channel (5, 6)
		self.inst.write('CN 5, 6')

	def cn_SMU(self):
		# Turn ON all SMU
		self.inst.write('CN 1, 3, 5, 6')

	def cn_MFCMU(self):
		# Turn on MFCMU channel (7)
		self.inst.write('CN 7')

	def err(self):
		# Return the last error
		self.inst.write('ERR? 1')
		b = self.inst.read()
		return int(b)

	def emg(self, err_num):
		# Return the error explanation by code
		b = "EMG? " + str(err_num)
		c = self.inst.query(b)
		return c

	def check_err(self, module_name = "None"):
		# Return error code and simple description
		b = self.err()
		if (b > 0):
			c = str(self.emg(b))
			print("Error code: ")
			print(b)
			print(c)
			d = "Module name: " + module_name
			e = str(b) + ": "
			logging.error(e + c + d, exc_info = False)
		return b

	def rst(self):
		# reset the B1500 to the initial settings
		self.inst.write('*RST')

	def clear_buf(self):
		# clear buffer before data receiving
		self.inst.write('FMT 1')

	def set_average_PLC(self, target_PLC):
		# Averaging in PLC (1 PLC == 20 ms)
		b = "AV -" + str(target_PLC) + ", 1"
		self.inst.write(b)

	def stop(self):
		# force 0V for all channels
		self.inst.write('DZ')
		
	def clear_timestamp(self):
		# set timestamp to 0
		# It might be useful for precise relaxation measurements.
		# To read the time data with the best resolution (100 us),
		# the timer must be cleared every 100 sec
		self.inst.write('TSR')

	def turn_on_channel_IV(self, ch_num, iv_state, V, I_lim):
		if (iv_state == 0):
			meas_type = 'DV'
		elif (iv_state == 1):
			meas_type = 'DI'
		else:
			return 000

		if (ch_num == 1):
			self.cn_HPSMU()
			inf_CN_gnd = "DV " + str(3) + ", 0, 0, " + str(1)
			inf_CN_meas = meas_type + " " + str(1) + ", 0, " + str(V) + ", " + str(I_lim)
			self.inst.write(inf_CN_gnd)
			self.inst.write(inf_CN_meas)
			return 310+self.check_err("turn_on_channel_IV")
		if (ch_num == 2):
			self.cn_MPSMU()
			inf_CN_gnd = "DV " + str(6) + ", 0, 0, " + str(0.1)
			inf_CN_meas = meas_type + " " + str(5) + ", 0, " + str(V) + ", " + str(I_lim)
			self.inst.write(inf_CN_gnd)
			self.inst.write(inf_CN_meas)
			return 320+self.check_err("turn_on_channel_IV")

	def turn_off_channel_IV(self, ch_num):
		if (ch_num == 1):
			self.inst.write('DZ 1')
			self.inst.write('DZ 3')
			return 410+self.check_err("turn_off_channel_IV")
		if (ch_num == 2):
			self.inst.write('DZ 5')
			self.inst.write('DZ 6')
			return 420+self.check_err("turn_off_channel_IV")
			
	def turn_channel_IV(self, ch_num, state, iv_state, V, I_lim):
		# This functios was separated from prepare_IV
		# for external LED illumination without IV measuring
		#
		# ch_num: 1 for 1-3 (HPSMU), 2 for 5-6 (MPSMU)
		# state: turn_ON (2) / turn_OFF (0)
		# iv_state: 0 for Voltage, 1 for Current
		# V - target Voltage (or current if iv_state == 1)
		# I_lim - Current limit (or voltage limit, if iv_state == 1)
		if (state):
			return self.turn_on_channel_IV(ch_num, iv_state, V, I_lim)
		else:
			return self.turn_off_channel_IV(ch_num)

	def test_measure_IV_point(self, CN_num_meas, CN_num_gnd, V, I_lim):
		# Example of IV measurement (single point)
		# Channel modification looks like:
		# 'DV 1, 0, 1, 0.1'
		# Where:
		# DV - function "Force DC voltage from the specified channel"
		# 1 - channel (HVSMU 1 in this case. 1 == HPSMU 1, 3 == HPSMU 2, 5 == MPSMU 3, 6 == MPSMU 4)
		# 0 - vrange (auto in this case)
		# 1 - target voltage, V
		# 0.1 - Current compliance value, A (0.1 or less for MPSMU, 1 or less for HPSMU)
		# Normally CN_meas = 1, CN_gnd = 3 for current <= 1 A, 
		# CN_meas = 5, CN_gnd = 6 for current <= 0.1 A, 
		inf_CN_gnd = "DV " + str(CN_num_gnd) + ", 0, 0, " + str(I_lim)
		inf_CN_meas = "DV " + str(CN_num_meas) + ", 0, " + str(V) + ", " + str(I_lim)

		self.clear_buf()
		self.rst()
		self.cn()
		self.inst.write('TSC 1')
		self.set_average_PLC(2)
		self.inst.write('FL 0')
		self.inst.write(inf_CN_gnd)
		self.inst.write(inf_CN_meas)
		self.inst.write('MM 1, 1')
		self.inst.write('CMM 1, 1')
		self.inst.write('RI 1, 0')
		
		if (self.check_err("test_measure_IV_point") != 0):
			return 0

		self.inst.write('TSR')
		self.inst.write('XE')
		self.inst.write('TSQ')
		self.inst.write('DZ')
		a = self.inst.read()
		b = self.inst.read()
		tcal = ""
		tret = ""
		for i in range(4, 4+12):
			tcal += a[i-1]
			tret += b[i-1]
		meas_status = ""
		for i in range(17, 17+3):
			meas_status += a[i-1]
		result = ""
		for i in range(20, 20+12):
			result += a[i-1]
		if (self.check_err("test_measure_IV_point") != 0):
			return 0
		return float(result)

	def prepare_IV(self, ch_num, iv_state, target_PLC = 2):
		# Prepare the channels for IV measurements:
		# - Clear buffer before receiving
		# - "TSC" enables time stamp
		# - set the averaging time
		# - "FL" sets the filter (or reset if filter is 0)
		#
		# ch_num comes from GUI and can be equal:
		#	0b00 == disable first channel (HPSMU 1, HPSMU3), disable second channel (MPSMU 1, MPSMU3)
		#	0b01 == enable first channel, disable second channel
		#	0b00 == disable first channel, enable second channel
		#	0b00 == enable first channel, enable second channel
		# (UNUSED NOW, see self.turn_channel_IV)
		# 
		# iv_state signalise measuring status and can be equal:
		#	0b00 == voltage from 1st channel, voltage from 2nd channel
		#	0b01 == current from 1st channel, voltage from 2nd channel
		#	0b10 == voltage from 1st channel, current from 2nd channel
		#	0b11 == current from 1st channel, current from 2nd channel
		# (UNUSED NOW, see self.turn_channel_IV)
		#
		# target_PLC is the averaging time in PLC units (I didn't add averaging in seconds)
		
		self.clear_buf()
		self.inst.write('TSC 1')
		self.set_average_PLC(target_PLC)
		self.inst.write('FL 0')
		b = self.check_err("prepare_IV")
		if (b != 0):
			return b
		return 0

	def measure_IV(self, target_channel, iv_state, V, I_lim):
		# Measure prepared IV (single channel only, single point)
		# - Modify the channels
		# - 'MM' - change measuremnet mode (== 1 for IV measurement)
		# - 'CMM' - change operation mode (== 1 for Current, ==2 for Voltage)
		# - 'RI' (or 'RV') - choose current (or voltage) range
		# - 'XE' - this command triggers the B1500 to start measurement
		# At the moment I read the data right after 'XE' and 'ERR?'. Is it correct?
		#
		# Channel modificator looks like:
		# 'DV 1, 0, 2, 0.1'
		# Where:
		#	DV - function "Force DC voltage from the specified channel"
		#	DI - function "Force DC voltage from the specified channel"
		#	1 - channel (HVSMU 1 in this case, 3 == HPSMU 2, 5 == MPSMU 3, 6 == MPSMU 4)
		#	0 - vrange (auto in this case)
		#	2 - target voltage, V
		#	0.1 - Current compliance value, A (0.1 or less for MPSMU, 1 or less for HPSMU)
		#
		# Agilent return looks like:
		#	['NAT+1.03147E+05', 'NAI+0.05090E-09\r\n']
		#	[0 ]NAT: time in seconds
		#	[1] NAI: current (s)
		
		if (target_channel == 1):
			CN_num_meas = 1
			CN_num_gnd = 3
			GND_I_lim = 1
			iv_state = iv_state & target_channel
		elif (target_channel == 2):
			CN_num_meas = 5
			CN_num_gnd = 6
			GND_I_lim = 0.1
			iv_state = (iv_state & target_channel) >> 1
		else:
			return 815

		if (iv_state == 0):
			inf_CN_gnd = "DV " + str(CN_num_gnd) + ", 0, 0, " + str(GND_I_lim)
			inf_CN_meas = "DV " + str(CN_num_meas) + ", 0, " + str(V) + ", " + str(I_lim)
		elif (iv_state == 1):
			inf_CN_gnd = "DV " + str(CN_num_gnd) + ", 0, 0, " + str(GND_I_lim)
			inf_CN_meas = "DI " + str(CN_num_meas) + ", 0, " + str(V) + ", " + str(I_lim)
		self.inst.write(inf_CN_gnd)
		self.inst.write(inf_CN_meas)
		
		if (self.check_err("measure_IV") != 0):
			return 0

		self.inst.write('MM 1, ' + str(CN_num_meas))
		self.inst.write('CMM ' + str(CN_num_meas) + ', ' + str(iv_state+1))
		if (iv_state == 0):
			self.inst.write('RI ' + str(CN_num_meas) + ', 0')
		elif (iv_state == 1):
			self.inst.write('RV ' + str(CN_num_meas) + ', 0')
		else:
			return 816

		self.inst.write('XE')

		e = self.check_err("measure_IV")
		if (e != 0):
			return e

		a = self.inst.read()
		ans = []
		for i in a.split(","):
			ans.append(float(i[3:]))
		return ans

	def test_measure_CV(self):
		# Example of CV measurement
		# MM 17: measure CV using MFCMU
		# IMP 100: measure Cp - G
		# LMN 1: enable data monitor
		# DCV 7, -0.1: 0.1 is the voltage
		# TTC 7, 0: 0 is the mode (auto range == 0, fixed range == 2)
		
		self.clear_buf()
		self.inst.write('TSC 1')
		self.inst.write('MM 17, 7')
		
		self.inst.write('FC 7, 1.1e3')
		self.inst.write('ACV 7, 0.1')

		self.inst.write('IMP 100') 
		self.inst.write('LMN 1')

		for i in range(-20, 5, 1):
			a = float(i)/10.0
			self.inst.write('DCV 7, ' + str(a))
			self.inst.write('TTC 7, 0')
			a = self.inst.read()
			print(a)
		return 0

	def prepare_CV(self, target_freq, target_osc, is_filter = 0):
		# Prepare MFCMU channel for CV measurement
		# - Turn on the channel, clear buffer before data receiving
		# - 'MM' - change measuremnet mode (== 17 for Spot C)
		# - 'FC' - set the frequency
		# - 'ACV' - set the oscyllation (in V units)
		# - 'IMP' - change measurement parameters (100 == Cp / G)
		# - 'LMN' - enable the data monitor and output
		#
		# Filter is not available for MFCMU! It is for SMU channels only!
		# I disable the "TSC" (timestamp function) to reduce the number of receiving data
		
		self.cn_MFCMU()
		self.clear_buf()
		#self.inst.write('TSC 1')
		self.inst.write('MM 17, 7')
		if (is_filter):
			self.inst.write('FL 1, 7')
		self.inst.write('FC 7, ' + str(target_freq))
		self.inst.write('ACV 7, ' + str(target_osc))
		self.inst.write('IMP 100') 
		self.inst.write('LMN 1')
		b = self.check_err("prepare_CV")
		if (b != 0):
			return b
		return 0

	def measure_CV(self, target_voltage, target_range = 0):
		# Measure prepared CV (single point)
		# - set the bias: 'DCV 7, -0.1' where 7 is the channel (MFCMU), -0.1 is the voltage
		# - set the range: 'TTC 7, 0' where 7 is the channel (MSCMU), 0 is the range
		# Range can be:
		#	0 for auto range
		#	100 for 100 Ohm impedance
		#	300 for 100 Ohm impedance
		#	and so on.
		#	Fixed raging modes:
		#	100, 300, 1000, 3000, 10000, 30000, 100000, 300000
		#	see table 4-17 and figure 4-1 in manual
		#
		# Agilent return looks like:
		# ['NGT+9.95448E+04', 'NGC+2.93985E-11', 'NGY+1.85398E-07', 'NGV+099.639E-03', 'NGV+1.00042E+00\r\n']
		# [0] NGT: time in seconds
		# [1] NGC: capacitance
		# [2] NGY: conductance
		# [3] NGV[0]: V osc
		# [4] NGV[1]: V bias
		# Of course, V bias is not necessarily equals to target_voltage
		
		self.inst.write('DCV 7, ' + str(target_voltage))
		if (target_range == 0):
			self.inst.write('TTC 7, 0')
		else:
			self.inst.write('TTC 7, 2, ' + str(target_range))
		e = self.check_err("measure_CV")
		if (e != 0):
			return e
		a = self.inst.read()
		ans = []
		for i in a.split(","):
			ans.append(float(i[3:]))
		return ans

	def test_measure_CF(self, target_freq, target_osc, target_voltage, target_range = 0):
		# Example of CF measurement
		# MM 17: measure CV using MFCMU
		# IMP 100: measure Cp - G
		# LMN 1: enable data monitor
		# DCV 7, -0.1: 0.1 is the voltage
		# TTC 7, 0: 0 is the range mode (auto range == 0, fixed range == 2)
		
		self.clear_buf()
		self.inst.write('TSC 1')
		self.inst.write('MM 17, 7')
		
		self.inst.write('FC 7, 1.1e3')
		self.inst.write('ACV 7, 0.1')

		self.inst.write('IMP 100') 
		self.inst.write('LMN 1')

		for i in range(-20, 5, 1):
			a = float(i)/10.0
			self.inst.write('DCV 7, ' + str(a))
			self.inst.write('TTC 7, 0')
			a = self.inst.read()
			print(a)
		return 0

	def prepare_CF(self, target_osc, target_voltage):
		# Prepare MFCMU channel for CV measurement
		# - Turn on the channel, clear buffer before data receiving
		# - 'TSC' - enable timestamp function
		# - 'MM' - change measuremnet mode (== 17 for Spot C)
		# - 'FC' - set the frequency in Hz (for B1500 it is 1000 - 5000000)
		# - 'ACV' - set the oscyllation (in V units)
		# - 'DCV' - set the bias (in V units)
		# - 'IMP' - change measurement parameters (100 == Cp / G)
		# - 'LMN' - enable the data monitor and output
		#
		# Filter is not available for MFCMU! It is for SMU channels only!
		
		self.cn_MFCMU()
		self.clear_buf()
		self.inst.write('TSC 1')
		self.inst.write('MM 17, 7')
		self.inst.write('FC 7, 1000')
		self.inst.write('ACV 7, ' + str(target_osc))
		self.inst.write('DCV 7, ' + str(target_voltage))
		self.inst.write('IMP 100') 
		self.inst.write('LMN 1')
		b = self.check_err("prepare_CF")
		if (b != 0):
			return b
		return 0

	def measure_CF(self, target_freq, target_range = 0):
		# Measure prepared CF (single point)
		# - set the qrequency
		# - set the range
		# - read the data
		#
		# 'target_freq' is the measurement prequency in Hz (1000 - 5000000 for B1500)
		# 'target_range' is the impedance range
		# Range can be:
		#	0 for auto range
		#	100 for 100 Ohm impedance
		#	300 for 100 Ohm impedance
		#	and so on.
		#	Fixed raging modes:
		#	100, 300, 1000, 3000, 10000, 30000, 100000, 300000
		#	see table 4-17 and figure 4-1 in manual
		#
		# Agilent return looks like:
		# ['NGT+9.95448E+04', 'NGC+2.93985E-11', 'NGY+1.85398E-07', 'NGV+099.639E-03', 'NGV+1.00042E+00\r\n']
		# [0] NGT: time in seconds
		# [1] NGC: capacitance
		# [2] NGY: conductance
		# [3] NGV[0]: V osc
		# [4] NGV[1]: V bias
		
		self.inst.write('FC 7, ' + str(target_freq))
		if (target_range == 0):
			self.inst.write('TTC 7, 0')
		else:
			self.inst.write('TTC 7, 2, ' + str(target_range))
		e = self.check_err("measure_CF")
		if (e != 0):
			return e
		a = self.inst.read()
		ans = []
		for i in a.split(","):
			ans.append(float(i[3:]))
		return ans

	def prepare_didlnt_point(self, V_diode, I_lim_diode, target_PLC = 2):
		# Prepare the channels for didlnt measurements:
		# - Clear buffer before receiving
		# - "TSC" enables time stamp
		# - set the averaging time in PLC
		# - "FL" sets the filter (or reset if filter is 0)
		#
		# Modify the channels:
		# - 'MM' - change measuremnet mode (== 1 for IV measurement)
		# - 'CMM' - change operation mode (== 1 for Current, ==2 for Voltage)
		# - 'RI' (or 'RV') - choose current (or voltage) range
		# target_PLC is the averaging time in PLC units (I didn't add averaging in seconds)
		#
		# Channel modificator looks like:
		# 'DV 1, 0, 2, 0.1'
		# Where:
		#	DV - function "Force DC voltage from the specified channel"
		#	DI - function "Force DC voltage from the specified channel"
		#	1 - channel (HVSMU 1 in this case, 3 == HPSMU 2, 5 == MPSMU 3, 6 == MPSMU 4)
		#	0 - vrange (auto in this case)
		#	2 - target voltage, V
		#	0.1 - Current compliance value, A (0.1 or less for MPSMU, 1 or less for HPSMU)
		
		self.clear_buf()
		self.inst.write('TSC 1')
		self.set_average_PLC(target_PLC)
		self.inst.write('FL 0')
		
		CN_diode_meas = 5
		CN_diode_gnd = 6
		GND_diode_I_lim = 0.1

		inf_CN_gnd = "DV " + str(CN_diode_gnd) + ", 0, 0, " + str(GND_diode_I_lim)
		inf_CN_meas = "DV " + str(CN_diode_meas) + ", 0, " + str(V_diode) + ", " + str(I_lim_diode)
		print(inf_CN_meas, inf_CN_gnd)
		self.inst.write(inf_CN_gnd)
		self.inst.write(inf_CN_meas)
		
		print("didlnt prepared")
		
		self.inst.write('MM 1, ' + str(5))
		self.inst.write('CMM ' + str(5) + ', ' + str(1))
		self.inst.write('RV ' + str(5) + ', 0')
		
		self.clear_timestamp()

		b = self.check_err("prepare_didlnt_point")
		if (b != 0):
			return b
		return 0

	def didlnt_switch_LED(self, I_LED, V_lim_LED):
		if (I_LED > 0):
			CN_LED_meas = 1
			CN_LED_gnd = 3
			GND_LED_I_lim = 1
			inf_CN_gnd = "DV " + str(CN_LED_gnd) + ", 0, 0, " + str(GND_LED_I_lim)
			inf_CN_meas = "DI " + str(CN_LED_meas) + ", 0, " + str(I_LED) + ", " + str(V_lim_LED)
			print(inf_CN_meas, inf_CN_gnd)
			self.inst.write(inf_CN_gnd)
			self.inst.write(inf_CN_meas)
			b = self.check_err("prepare_didlnt_point")
			if (b != 0):
				return b
			return 0b0001
		if (I_LED == 0):
			self.inst.write('DZ 1')
			self.inst.write('DZ 3')
			return 410+self.check_err("turn_off_channel_IV")

	def measure_didlnt_point(self):
		# Measure prepared didlnt (single channel only, single point)
		# - 'XE' - this command triggers the B1500 to start measurement
		#
		# Channel modificator looks like:
		# 'DV 1, 0, 2, 0.1'
		# Where:
		#	DV - function "Force DC voltage from the specified channel"
		#	DI - function "Force DC voltage from the specified channel"
		#	1 - channel (HVSMU 1 in this case, 3 == HPSMU 2, 5 == MPSMU 3, 6 == MPSMU 4)
		#	0 - vrange (auto in this case)
		#	2 - target voltage, V
		#	0.1 - Current compliance value, A (0.1 or less for MPSMU, 1 or less for HPSMU)
		#
		# Agilent return looks like:
		#	['NAT+1.03147E+05', 'NAI+0.05090E-09\r\n']
		#	[0 ]NAT: time in seconds
		#	[1] NAI: current (s)
		
		self.inst.write('XE')

		a = self.inst.read()
		ans = []
		for i in a.split(","):
			ans.append(float(i[3:]))
		return ans
	
	def prepare_point_for_fast_IV(self, chan, regime, V_diode, I_lim_diode, target_PLC = 2):
		# Prepare the channels for IV measurements:
		# - Clear buffer before receiving
		# - "TSC" enables time stamp
		# - set the averaging time in PLC
		# - "FL" sets the filter (or reset if filter is 0)
		#
		# Modify the channels:
		# - 'MM' - change measuremnet mode (== 1 for IV measurement)
		# - 'CMM' - change operation mode (== 1 for Current, ==2 for Voltage measurement)
		# - 'RI' (or 'RV') - choose current (or voltage) range
		# target_PLC is the averaging time in PLC units (I didn't add averaging in seconds)
		#
		# Channel modificator looks like:
		# 'DV 1, 0, 2, 0.1'
		# Where:
		#	DV - function "Force DC voltage from the specified channel"
		#	DI - function "Force DC voltage from the specified channel"
		#	1 - channel (HVSMU 1 in this case, 3 == HPSMU 2, 5 == MPSMU 3, 6 == MPSMU 4)
		#	0 - vrange (auto in this case)
		#	2 - target voltage, V
		#	0.1 - Current compliance value, A (0.1 or less for MPSMU, 1 or less for HPSMU)
		
		if ((chan != 1) and (chan != 2)):
			print("channel error")
			return -1
		
		if ((regime != 0) and (regime != 1)):
			print("regime error")
			return -2

		self.clear_buf()
		self.inst.write('TSC 1')
		self.set_average_PLC(target_PLC)
		self.inst.write('FL 0')
		
		if (chan == 1):
			CN_diode_meas = 1
			CN_diode_gnd = 3
			GND_diode_I_lim = 1
		if (chan == 2):
			CN_diode_meas = 5
			CN_diode_gnd = 6
			GND_diode_I_lim = 0.1
			

		if (regime == 0):
			# set voltage, measure current
			meas_reg_string = "DV"
			range_reg_string = "RI"
			meas_regime = 1
		if (regime == 1):
			meas_reg_string = "DI"
			range_reg_string = "RV"
			meas_regime = 2
			
		inf_CN_gnd = "{0} {1:.0f}, {2:.0f}, {3:e}, {4:e}".format("DV", CN_diode_gnd, 0, 0, GND_diode_I_lim)
		inf_CN_meas = "{0} {1:.0f}, {2:.0f}, {3:e}, {4:e}".format(meas_reg_string, CN_diode_meas, 0, V_diode, I_lim_diode)
		
		#print(inf_CN_meas, " | ", inf_CN_gnd)
		self.inst.write(inf_CN_meas)
		self.inst.write(inf_CN_gnd)
		
		self.inst.write("MM {0:d}, {1:d}".format(1, CN_diode_meas))
		self.inst.write("CMM {0:d}, {1:d}".format(CN_diode_meas, meas_regime))
		self.inst.write("{0} {1:d}, {2:d}".format(range_reg_string, CN_diode_meas, 0))
		
		print("Point measurements prepared")
		
		self.clear_timestamp()

		b = self.check_err("prepare_IT_point")
		if (b != 0):
			return b
		return 0
	
	def measure_fast_IV_point(self):
		# Measure prepared IV point (single channel only, single point)
		# - 'XE' - this command triggers the B1500 to start measurement
		#
		# Agilent return looks like:
		#	['NAT+1.03147E+05', 'NAI+0.05090E-09\r\n']
		#	[0] NAT: time in seconds
		#	[1] NAI: current (A)
		# If B1500 forces current and measures voltage, answer is 'NAV+1.578E-5'
		
		self.inst.write('XE')

		a = self.inst.read()
		ans = []
		for i in a.split(","):
			ans.append(float(i[3:]))
		return ans
		
	def prepare_DLTS(self, freq, V_bias, V_osc, V_pulse, t_pulse, t_step, N_steps, t_hold_after = 0, target_range = 0):
		# B1500.prepare_DLTS(1000, -1, 0.1, 1, 0.05, 0.01, 100)
		self.inst.write('FMT 1, 1')
		self.inst.write('TSC 1')
		self.inst.write('MM 26, 7')
		self.inst.write('FC 7, {0:f}'.format(freq))
		self.inst.write('ACV 7, {0:f}'.format(V_osc))
		self.inst.write('DCV 7, {0:f}'.format(V_bias))
		self.inst.write('IMP 100')
		if (target_range > 0):
			self.inst.write('RC 7, 2, {0:d}'.format(target_range))
		else:
			self.inst.write('RC 7, 0')
		self.inst.write('MDCV 7, {0:.3f}, {1:.3f}, {1:.3f}'.format(V_pulse, V_bias))
		#print('MDCV 7, {0:.3f}, {1:.3f}, {1:.3f}'.format(V_pulse, V_bias))
		self.inst.write('MTDCV 0, {0:.3f}, {1:d}, {2:.2f}'.format(t_step, N_steps, t_hold_after))
		#print('MTDCV 0, {0:.3f}, {1:d}, {2:.2f}'.format(t_step, N_steps, t_hold_after))
		
		b = self.check_err("prepare_IT_point")
		if (b != 0):
			return b
		return 0
		
	def set_voltage_DLTS(self, V_pulse):
		#print('DCV 7, {0:.3f}'.format(V_pulse))
		self.inst.write('TSR')
		self.inst.write('DCV 7, {0:.3f}'.format(V_pulse))
		
	def measure_DLTS(self, t_sleep):
		# B1500.measure_DLTS(1, 0.05, 0.01, 100)
		#print(t_step*N_steps+t_hold_after + 1)
		#print('DCV 7, {0:.3f}'.format(V_pulse))
		#self.inst.write('TSR')
		#self.inst.write('DCV 7, {0:.3f}'.format(V_pulse))
		#time.sleep(t_pulse)
		self.inst.write('XE')
		time.sleep(t_sleep + 1)
		ans = self.inst.read()
		return ans
	
	def begin_measure_and_read_answer(self, t_sleep):
		self.inst.write('XE')
		time.sleep(t_sleep)
		ans = self.inst.read()
		return ans
		
class K33510B(scpi_device):
	_inst = None
	_device_address = 'TCPIP0::K-33510B-02034::inst0::INSTR'

	def err(self):
		a = self._inst.query("SYST:ERR?")
		return a

	def prepare_trigger_chan(self, target_channel, target_period):
		self._inst.write('OUTP{0:d} 0'.format(target_channel))
		self._inst.write('SOUR{0:d}:FUNC SQU'.format(target_channel))
		self._inst.write('SOUR{0:d}:FUNC:SQU:DCYC {1:.2f}'.format(target_channel, 20))
		self._inst.write('OUTP{0:d}:LOAD INF'.format(target_channel))
		self._inst.write('SOUR{0:d}:VOLT:HIGH {1:f}'.format(target_channel, 5.0))
		self._inst.write('SOUR{0:d}:VOLT:LOW {1:f}'.format(target_channel, 0.0))
		self._inst.write('SOUR{0:d}:FUNC:SQU:PER {1:e}'.format(target_channel, target_period))
	
	def trigger_start(self, target_channel):
		self._inst.write('OUTP{0:d} 1'.format(target_channel))
		return target_channel
	
	def trigger_stop(self, target_channel):
		self._inst.write('OUTP{0:d} 0'.format(target_channel))
		return target_channel

class TH2836(scpi_device):
	# Tonghui TH2836 LCR meter.
	# As a SCPI device, it inherits the following functions:
	# - connect(self)
	# - get_status(self)
	# - white(self, target_text)
	# - read(self)
	# - query(self, target_text)
	# - close_connection(self)
	# - idn(self)
	#
	# Known problems:
	# (!) Read_termination byte is not NONE bot 0x0A (== \r)
	# (!) The device freezes when the operator asks
	#		> inst.query('DISP:PAGE?')
	# 
	 
	def __init__(self):
		super().__init__()
		self.model_type = 'TH2836'
		self.device_address = 'TCPIP0::192.168.10.135::8000::SOCKET'
		self.read_termination = chr(0x0A)
		self.connect()
		self.wait_before_fetch = 0.1 # seconds
		self.current_frequency = 1000 # Hz
		self.current_speed = "MED"
		self.current_averaging = 1
	
	def set_frequency(self, target_frequency):
		# Set the frequency (in Hz)
		if not isinstance(target_frequency, (int, float)):
			print("Error: target_frequency is not a number")
			return -2			
		if target_frequency < 4:
			print("Target frequency is too low")
			return 0
		if target_frequency > 8.5e6:
			print("Target frequency is too hihg")
			return -1
		try:
			self.current_frequency = target_frequency
			self.write("FREQ {0:.3f} Hz".format(target_frequency))
			self.find_delay_before_fetch()
		except Exception as e:
			print("{0:s} set_frequency error: {1:s}".format(self.model_type, str(e)))
			return -3
		return target_frequency
		
	def set_voltage(self, target_voltage):
		# Set the the measurement (AC) level voltage of the instrument
		# Volatge range is 5mV(RMS) - 2V(RMS), step 100 uV
		if not isinstance(target_voltage, (int, float)):
			print("Error: target_frequency is not a number")
			return -2
		target_voltage = abs(target_voltage)
		if target_voltage < 5e-3:
			print("Target voltage is too low")
			return 0
		if target_voltage > 2:
			print("Target voltage is too hihg")
			return -1
		try:
			self.write("VOLT {0:.4f}V".format(target_voltage))
		except Exception as e:
			print("{0:s} set_voltage error: {1:s}".format(self.model_type, str(e)))
			return -3
		return target_voltage

	def set_bias_voltage(self, target_voltage):
		# Set the DC bias voltage (in V)
		if not isinstance(target_voltage, (int, float)):
			print("Error: target_frequency is not a number")
			return -2			
		if target_voltage < -40:
			print("Target voltage is too low")
			return 0
		if target_voltage > 40:
			print("Target voltage is too hihg")
			return -1
		try:
			self.write("BIAS:VOLT {0:.4f}V".format(target_voltage))
		except Exception as e:
			print("{0:s} set_bias_voltage error: {1:s}".format(self.model_type, str(e)))
			return -3
		return target_voltage
	
	def set_bias_state(self, target_status):
		# If status == 0 or status == false thet turn BIAS off,
		# else turn BIAS on
		try:
			if bool(target_status):
				self.write("BIAS:STAT 1")
			else:
				self.write("BIAS:STAT 0")
		except Exception as e:
			print("{0:s} set_bias_state error: {1:s}".format(self.model_type, str(e)))
			self.status = "Error"
		finally:
			return self.status
		
	def set_function(self, target_key):
		# dictionary of possible functions for TH2836.
		# Important values: 
		# 1 - Cp / D
		# 5 - Cp / G
		# 7 - Cp / Rp
		# 9 - Cs / D

		if not isinstance(target_key, (int, float)):
			print("Error: target_key is not a number")
			return -2
		if (target_key < 0) or (target_key > 23):
			print("Error: wrong target_key")
			return -1

		lcr_functions = {
			1: "CPD",		# Sets "Function" to Cp-D.
			2: "LPRP",		# Sets "Function" to Lp-Rp.
			3: "CPQ",		# Sets "Function" to Cp-Q.
			4: "LSD",		# Sets "Function" to Ls-D.
			5: "CPG",		# Sets "Function" to Cp-G.
			6: "LSQ",		# Sets "Function" to Ls-Q.
			7: "CPRP",		# Sets "Function" to Cp-Rp.
			8: "LSRS",		# Sets "Function" to Ls-Rs.
			9: "CSD",		# Sets "Function" to Cs-D.
			10: "RX",		# Sets "Function" to R-X.
			11: "CSQ",		# Sets "Function" to Cs-Q.
			12: "ZTD",		# Sets "Function" to Z-theta.
			13: "CSRS",		# Sets "Function" to Cs-Rs.
			14: "ZTR",		# Sets "Function" to Z-theta_r.
			15: "LPQ",		# Sets "Function" to Lp-Q.
			16: "GB",		# Sets "Function" to G-B.
			17: "LPD",		# Sets "Function" to Lp-D.
			18: "YTD",		# Sets "Function" to Y-theta.
			19: "LPG",		# Sets "Function" to Lp-G.
			20: "YTR",		# Sets "Function" to Y-theta_r.
			21: "LPRD",		# Sets "Function" to Lp-Rd.
			22: "RPQ",		# Sets "Function" to Rp-Q.
			23: "LSRD",		# Sets "Function" to Ls-Rd.
		}
		
		try:
			self.write("FUNC:IMP {0:s}".format(lcr_functions[int(target_key)]))
		except Exception as e:
			print("{0:s} set_voltage error: {1:s}".format(self.model_type, str(e)))
			return 0
		return target_key
	
	def set_impedance_range(self, target_impedance_range):
		# This function sets the range for quasy-static measurements (of impedance)
		# Only number of values can be used as range:
		# - 0.1, 1, 10, 20, 50, 100, 200, 500, 1000, 
		#   2000, 5000, 10000, 20000, 50000, 100000 Ohms
		# Also we can use the Auto_range regime (I call it 0 Ohm),
		# so, you can choose 0 or any number from the list
		
		if not isinstance(target_impedance_range, (int, float)):
			print("Error: target_impedance_range is not a number")
			return -2
		
		list_of_ranges = [0, 0.1, 1, 10, 20, 50, 100, 200, 500, 1000,  2000, 5000, 10000, 20000, 50000, 100000]
		target_range = min(list_of_ranges, key=lambda x: abs(x - target_impedance_range))
		
		if (abs(target_range - target_impedance_range) > 1e-3):
			print("Target range is not allowed. Used {0:f} instead of {1:f} Ohm".format(target_range,target_impedance_range))
		
		try:
			if (target_range == 0):
				self.write("FUNC:IMP:RANG:AUTO ON")
			else:
				self.write("FUNC:IMP:RANG:AUTO OFF")
				if (target_range == 0.1):
					self.write("FUNC:IMP:RANG 0.1OHM")
				else:
					self.write("FUNC:IMP:RANG {0:d}OHM".format(target_range))
			return target_range
		except Exception as e:
			print("{0:s} set_impedance_range error: {1:s}".format(self.model_type, str(e)))
			return -1
				
	def set_resistance_range(self, target_resistance_range):
		# This function sets the range for statis measurements (of resistance)
		# Only number of values can be used as range:
		# - 0.1, 1, 10, 20, 50, 100, 200, 500, 1000, 
		#   2000, 5000, 10000, 20000, 50000, 100000 Ohms
		# Also we can use the Auto_range regime (I call it 0 Ohm),
		# so, you can choose 0 or any number from the list
		
		if not isinstance(target_resistance_range, (int, float)):
			print("Error: target_resistance_range is not a number")
			return -2
		
		list_of_ranges = [0, 0.1, 1, 10, 20, 50, 100, 200, 500, 1000,  2000, 5000, 10000, 20000, 50000, 100000]
		target_range = min(list_of_ranges, key=lambda x: abs(x - target_resistance_range))
		
		if (abs(target_range - target_resistance_range) > 1e-3):
			print("Target range is not allowed. Used {0:f} instead of {1:f} Ohm".format(target_range,target_resistance_range))
		
		try:
			if (target_range == 0):
				self.write("FUNC:DCR:RANG:AUTO ON")
			else:
				self.write("FUNC:DCR:RANG:AUTO OFF")
				if (target_range == 0.1):
					self.write("FUNC:DCR:RANG 0.1OHM")
				else:
					self.write("FUNC:DCR:RANG {0:d}OHM".format(target_range))
			return target_range
		except Exception as e:
			print("{0:s} set_resistance_range error: {1:s}".format(self.model_type, str(e)))
			return -1
		
	def set_aperture(self, target_speed, target_averaging = 1):
		# speed can be:
		# - "SLOW":		Slow, 4 times per second.
		# - "MEDium":	Medium, 11 times per second. 
		# - "FAST":		Fast, 130 times per second. 
		# From 3.1.6.1 "Speed Range" (TH2836 manual):
		# Freq	| Fast	| Med	| Slow
		# 20	| 380	| 380	| 480
		# 100	| 100	| 180	| 300
		# 1K	| 20	| 110	| 240
		# 10K	| 7.7	| 92	| 230
		# 100K	| 5.7	| 89	| 220
		# 1M	| 5.6	| 88	| 220
		# 8.5M	| 5.6	| 88	| 220

		if not isinstance(target_averaging, (int, float)):
			print("Error: target_resistance_range is not a number")
			return -2
		target_averaging = int(target_averaging)
		if target_averaging < 1:
			print("Error: target_resistance_range is lower than 1")
			return -3
		if target_averaging > 255:
			print("Error: target_resistance_range is greater than 255")
			return -4
		
		list_of_speeds = ["FAST", "MED", "MEDIUM", "SLOW"]
		target_speed = target_speed.upper()
		if (target_speed in list_of_speeds):
			try:
				self.current_averaging = target_averaging
				self.current_speed = target_speed
				self.write("APER {0:s},{1:d}".format(target_speed, target_averaging))
				self.find_delay_before_fetch()
				return target_averaging
			except Exception as e:
				print("{0:s} set_aperture error: {1:s}".format(self.model_type, str(e)))
				return -1
		else:
			print("Error with speed naming: {0:s} is not an allowed value".format(target_speed))
			return 0
		
	def set_step_delay(self, target_step_delay):
		# set_delay is the time between the output of the test signal maintaining
		# and the beginning of measurement (see fig. 4.2 in TH2836 manual)
		if not isinstance(target_step_delay, (int, float)):
			print("Error: target_step_delay is not a number")
			return -2
		if target_step_delay < 0:
			print("Error: target_step_delay is lower than 0 s")
			return -3
		if target_step_delay > 60:
			print("Error: target_step_delay is greater than 60 s")
			return -4
		
		try:
			self.write("FUNC:SDEL {0:.3f}S".format(target_step_delay))
			return target_step_delay
		except Exception as e:
			print("{0:s} set_step_delay error: {1:s}".format(self.model_type, str(e)))
			return -1
		
	def fetch(self):
		# Causes the TH2836 to send the result of the last measurement 
		# to the TH2836's output buffer.
		#
		# (!)
		# You neet to trigger the measurement before fetch. For example:
		# > inst.write("TRIG:SOUR BUS")
		# > inst.write("TRIG:IMM")
		# > inst.write("FETCH?")
		# > inst.read()
		try:
			self.write("FETC?")
			a = self.read()
		except Exception as e:
			print("{0:s} set_step_delay error: {1:s}".format(self.model_type, str(e)))
			a = ""
		finally:
			return a
		
	def set_trigger_source(self, target_source):
		# Trigger source can be:
		# - "INT" - internal (by internal module or measurement subsystems)
		# - "EXT" - external (by "Trigger" BNC connector)
		# - "BUS" - triggered by external source via RS232, GPIB or LAN (programming regime)
		# - "HOLD" - manual (by pressing the soft key on the front panel)
		trigger_list = ["INT", "EXT", "BUS", "HOLD"]
		target_source = target_source.upper()
		if (target_source in trigger_list):
			try:
				self.write("TRIG:SOUR {0:s}".format(target_source))
			except Exception as e:
				print("{0:s} set_trigger_source error: {1:s}".format(self.model_type, str(e)))
			return 0
		else:
			print("The trigger source is not in the list: \"{0:s}\"".format(target_source))
			return -1
		
	def set_trigger_delay(self, target_trigger_delay):
		# Trigger delay is the time between the triggering
		# and the beginning of measurement (see 4.1.4 in TH2836 manual)
		if not isinstance(target_trigger_delay, (int, float)):
			print("Error: set_trigger_delay is not a number")
			return -2
		if target_trigger_delay < 0:
			print("Error: set_trigger_delay is lower than 0 s")
			return -3
		if target_trigger_delay > 60:
			print("Error: set_trigger_delay is greater than 60 s")
			return -4
		
		try:
			self.write("TRIG:DEL {0:.3f}S".format(target_trigger_delay))
			return target_trigger_delay
		except Exception as e:
			print("{0:s} set_trigger_delay error: {1:s}".format(self.model_type, str(e)))
			return -1
		
	def trigger(self):
		try:
			self.write("TRIG:IMM")
			return 0
		except Exception as e:
			print("{0:s} trigger error: {1:s}".format(self.model_type, str(e)))
			return -1
		
	def find_delay_before_fetch(self):
		frequency_list = [20, 100, 1000, 10000, 100000, 1000000, 8500000]
		speed_dict = {"FAST": 1,"MED": 2,"MEDIUM": 2,"SLOW": 3}
		timer_list = []
		timer_list.append([ 4	, 380	, 380	, 480	])
		timer_list.append([ 20	, 380	, 380	, 480	])
		timer_list.append([ 100	, 100	, 180	, 300	])
		timer_list.append([ 1000	, 20	, 110	, 240	])
		timer_list.append([ 10000	, 7.7	, 92	, 230	])
		timer_list.append([ 100000	, 5.7	, 89	, 220	])
		timer_list.append([ 1000000	, 5.6	, 88	, 220	])
		
		temp_t = 0
		for i in timer_list:
			if (i[0] <= self.current_frequency):
				temp_t = i[speed_dict[self.current_speed]]
		temp_t = temp_t/1000*self.current_averaging + 0.1
		temp_t *= 2
		if self.current_frequency < 1000:
			temp_t *= 2
		if self.current_frequency < 20:
			temp_t *= 2
		self.wait_before_fetch = temp_t
		#print("Waiting time = " + str(temp_t))
		return temp_t
	
	def prepare_CF(self, target_osc, target_voltage):
		self.set_trigger_source("BUS")
		self.set_function(5)
		self.set_impedance_range(0)
		self.set_aperture("MED", 1)
		self.set_voltage(target_osc)
		self.set_bias_voltage(target_voltage)
		self.set_bias_state(1)
		return 0

	def measure_CF(self, target_freq, target_range = 0):
		# Measure prepared CF (single point)
		# - set the qrequency
		# - set the range
		# - read the data
		#
		# 'target_freq' is the measurement prequency in Hz (1000 - 5000000 for B1500)
		# 'target_range' is the impedance range
		# Range can be:
		#	0 for auto range
		#	100 for 100 Ohm impedance
		#	300 for 100 Ohm impedance
		#	and so on.
		#	Fixed raging modes:
		#	100, 300, 1000, 3000, 10000, 30000, 100000, 300000
		#	see table 4-17 and figure 4-1 in manual
		#
		# Agilent return looks like:
		# ['NGT+9.95448E+04', 'NGC+2.93985E-11', 'NGY+1.85398E-07', 'NGV+099.639E-03', 'NGV+1.00042E+00\r\n']
		# [0] NGT: time in seconds
		# [1] NGC: capacitance
		# [2] NGY: conductance
		# [3] NGV[0]: V osc
		# [4] NGV[1]: V bias
		
		self.set_frequency(target_freq)
		self.set_impedance_range(target_range)
		self.trigger()
		time.sleep(self.wait_before_fetch)
		#print(target_freq, target_range, self.wait_before_fetch)
		a = self.fetch()
		#time.sleep(self.wait_before_fetch)
		ans = [time.time()]
		for i in a.split(","):
			ans.append(float(i))
		return ans
	
	def stop(self):
		self.set_bias_state(0)
		self.set_trigger_source("INT")
		
class B2987(scpi_device):
	# Keysight B2987B picoammeter / 1000V source.
	# As a SCPI device, it inherits the following functions:
	# - connect(self)
	# - get_status(self)
	# - white(self, target_text)
	# - read(self)
	# - query(self, target_text)
	# - close_connection(self)
	# - idn(self)
	
	def __init__(self):
		super().__init__()
		self.model_type = 'B2987B'
		self.device_address = 'TCPIP::192.168.2.11::INSTR'
		self.connect()
		
	def check_error(self):
		try:
			self.write(":SYST:ERR?")
			a = self.read()
			b = int(a.split(",")[0])
			if (b == 0):
				return 0
			else:
				print("Error {0:d}: {1:s}".format(b, a.split(",")[1]))
				return b
		except Exception as e:
			print("Global error in check_errors module: {0:s}".format(e))
	
	def turn_input(self, target_status = True):
		if target_status:
			self.write(":INP:STAT ON")
		else:
			self.write(":INP:STAT OFF")
	
	def set_meas_mode(self, target_mode):
		# B2987B can measure:
		# - current ("CURR")
		# - charge ("CHAR")
		# - voltage ("VOLT")
		# - resistance ("RES")
		# Modes can be combined:
		# - resistance + current ("CURR", "RES")
		# - voltage + current ("CURR", "VOLT")
		# - voltage + current + resistance ("CURR", "VOLT", "RES")
		# etc.
		# You can add it manually if needed.
		self.write(':SENS:FUNC:ON {0:s}'.format(target_mode))
		
	def set_mode_current(self):
		self.set_meas_mode('"CURR"')

	def set_mode_resistance(self):
		self.set_meas_mode('"CURR", "RES"')
		
	def set_mode_voltage(self):
		self.set_meas_mode('"VOLT"')
		
	def shot_measure(self, target_mode = None):
		# Triggers measure of:
		# - current ("CURR")
		# - voltage ("VOLT")
		# - resistance ("RES")
		# - charge ("CHAR")
		#
		# If mode is None, device will measure all values,
		# in that case output will contain next values:
		# - voltage,
		# - current(charge),
		# - resistance,
		# - time,
		# - status,
		# - source,
		# - temperature,
		# - humidity
		
		if target_mode is None:
			self.write(':MEAS?'.format(target_mode))
		else:
			self.write(':MEAS:{0:s}?'.format(target_mode))
		
	def shot_measure_and_read(self, target_mode = None):
		# Triggers measure of:
		# - current ("CURR")
		# - voltage ("VOLT")
		# - resistance ("RES")
		# - charge ("CHAR")
		# and returns the STRING as an answer.
		#
		# If mode is None, device will measure all values,
		# in that case output will contain next values:
		# - voltage,
		# - current(charge),
		# - resistance,
		# - time,
		# - status,
		# - source,
		# - temperature,
		# - humidity
		
		if target_mode is None:
			self.write(':MEAS?'.format(target_mode))
		else:
			self.write(':MEAS:{0:s}?'.format(target_mode))
		a = self.read()
		return a

	def shot_measure_current(self):
		return self.shot_measure("CURR")
	
	def shot_measure_resistance(self):
		return self.shot_measure("RES")
		
	def set_voltage(self, target_voltage):
		try:
			target_voltage = float(target_voltage)
		except Exception as e:
			print("volatge convertion error: {0:s}".format(e))
			return -1
		if abs(target_voltage) > 1050:
			print("Overvoltage danger, voltage is not set")
			return -2
		self.write(":SOUR:VOLT:LEV:IMM:AMPL {0:.3f}".format(target_voltage))
	
	def turn_output(self, target_status = True):
		if target_status:
			self.write(":OUTP:STAT ON")
		else:
			self.write(":OUTP:STAT OFF")
		
	def add_r_lim(self, target_status = True):
		if target_status:
			self.write(":SOUR:VOLT:RLIM:STAT 1")
		else:
			self.write(":SOUR:VOLT:RLIM:STAT 0")

	def set_voltage_range(self, target_range):
		try:
			target_range = float(target_range)
		except Exception as e:
			print("volatge convertion error: {0:s}".format(e))
			return -1
		if abs(target_range) > 1050:
			print("Overvoltage danger, voltage range is not set")
			return -2
		self.write(":SOUR:VOLT:RANG {0:.3f}".format(target_range))

	def abort(self):
		self.write(":ABOR:ALL")
		
	def set_aperture_time(self, target_time):
		target_time = float(target_time)
		target_string = ":SENS:CURR:DC:APER {0:.3g}".format(target_time)
		self.write(target_string)
		
	def set_aperture_PLC(self, target_PLC):
		target_time = float(target_PLC)*0.02
		self.set_aperture_time(target_time)
		
	
