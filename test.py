import device
import time

class Test:
    DM3068 = None
    TH1991 = None

    def __init__(self):
        self.DM3068 = device.DM3068()
        self.TH1991 = device.TH1991()

        self.DM3068.set_function('VOLT')

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
            self.TH1991.output_enable()
            for i in range(num_cycles):
                voltage = self.DM3068.shot_measure_and_read()
                print(f"result {i}: {voltage} V")
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
    resistance = test.measure_res(current_amp=1e-9, voltage_limit_v=5, num_cycles=15)
    print(f"Res: {resistance} Ohms")

if __name__ == '__main__':
    main()
