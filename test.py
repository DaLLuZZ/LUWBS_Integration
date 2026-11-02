import device
import time

class Test:
    DM3068 = None
    TH1991 = None
    SWITCH = None

    def __init__(self):
        self.SWITCH = device.LUWBS_Switch()
        self.TH1991 = device.TH1991()
        #self.DM3068 = device.DM3068()

        #self.DM3068.set_function('VOLT')
        time.sleep(1)

    # inputs:
    # current value (A)
    # voltage limit for current source (V)
    # num of cycles (optional, default 1)
    # return: resistance value in Ohms (float)
    def measure_res(self, current_amp, voltage_limit_v, num_cycles = 1):
        res = self.TH1991.output_prepare('CURR', current_amp, voltage_limit_v)
        if (res != 0):
            print(f"Current source preparation error")
            return -1

        accum_volt = 0.0
        try:
            self.TH1991.enable_remote()
            self.TH1991.set_meas_range()
            self.TH1991.output_enable()
            for i in range(num_cycles):
                #voltage = self.DM3068.shot_measure_and_read()
                voltage = self.TH1991.shot_measure_and_read()
                #print(f"result {i}: {voltage} V")
                accum_volt = accum_volt + voltage
        except Exception as e:
            print(f"Error during resistance measurement: {e}")
            return -1

        self.TH1991.output_disable()

        avg_volt = accum_volt / num_cycles
        #print(f"avg per {num_cycles} cycles: {voltage} V")

        return abs(avg_volt / current_amp)

def main():
    test = Test()

    closure_seq = [
        ["0!0", "1!1", "2!2", "3!3"],
        ["0!2", "1!3", "2!0", "3!1"],
        #["0!0", "1!1", "2!3", "3!2"],
        #["0!1", "1!0", "2!2", "3!3"],
    ]
    test.SWITCH.set_closure_sequence(closure_seq)

    for i in range(1):
        if test.SWITCH.close_next() == 0:
            resistance = test.measure_res(current_amp=100e-9, voltage_limit_v=2, num_cycles=500)
            print(f"Res {i}: {resistance} Ohms")
        else: # error
            break
    
    test.SWITCH.open_all()

if __name__ == '__main__':
    main()
