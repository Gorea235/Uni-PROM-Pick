#! /usr/bin/env python3
from bus_wrapper import BusWrapper
import time
import threading
from timeout import Timeout

BUS_ID = 1
BUS_ADDR_PICK = 0x38
BUS_ADDR_DDISP = 0x24  # ????
# [row][column]
DIGIT_CONVERT = [
    ["1", "2", "3"],
    ["4", "5", "6"],
    ["7", "8", "9"],
    ["*", "0", "#"],
]
N_ROWS = len(DIGIT_CONVERT)
N_COLS = len(DIGIT_CONVERT[0])
USE_INTERRUPT = False
INTERRUPT_GPIO = 17
PASSWORD_LENGTH = 4
LED_WAIT_TIME = 1
PREVIOUS_WAIT_TIME = 0.5
DIGIT_CLEAR_TIME = 1


class BusAccessor:
    def __init__(self):
        self._buswrap = BusWrapper(BUS_ID)
        self._pick_id = "pick"
        self._ddisp_id = "ddisp"
        self._buswrap.add_addr(self._pick_id, BUS_ADDR_PICK)
        self._buswrap.add_addr(self._ddisp_id, BUS_ADDR_DDISP)

    # == digit meanings ==
    # 0 -> column 0
    # 1 -> column 1
    # 2 -> column 2
    # 3 -> led
    # 4 -> row 0
    # 5 -> row 1
    # 6 -> row 2
    # 7 -> row 3

    @property
    def pick(self):
        return self._buswrap[self._pick_id]

    @property
    def pick_led(self):
        return self.pick[3]

    @pick_led.setter
    def pick_led(self, value):
        assert isinstance(value, bool)
        self.pick[3] = value

    def pick_getcol(self, col):
        assert 0 <= col <= 2
        return self.pick[col]

    def pick_setcol(self, col, value):
        assert 0 <= col <= 2
        assert isinstance(value, bool)
        self.pick[col] = value

    def pick_getrow(self, row):
        assert 0 <= row <= 3
        return self.pick[row + 4]

    def pick_setrow(self, row, value):
        assert 0 <= row <= 3
        self.pick[row + 4] = value

    def pick_def(self):
        for i in range(len(self.pick)):
            self.pick[i] = False
        self.pick_led = True

    @property
    def ddisp(self):
        return self._buswrap[self._ddisp_id]


class Interface:
    def __init__(self, brute_force, logger):
        self.logger = logger

        self.bus = BusAccessor()
        self.brute = brute_force
        self.led_timer = Timeout(LED_WAIT_TIME)
        self.led_timer.elapsed.bind(self.led_timer_elapsed)
        self.led_wait_time_done = False
        self.led_waiter = threading.Event()
        self._do_loop = True

    def crack_password(self):
        if self.brute:
            pass  # perform brute force search
        else:
            found = []
            self.bus.pick_def()
            self.bus.pick.write_byte()
            self.disp_digit(None)
            input("Press enter to start the crack")
            while self._do_loop:
                #input("> do next loop <")
                found_digit = False
                for r in range(N_ROWS):
                    for c in range(N_COLS):
                        #input("> do next digit test ('{}')({},{}) <".format(DIGIT_CONVERT[r][c], r,c))
                        self.bus.pick_def()
                        time.sleep(DIGIT_CLEAR_TIME)
                        for f in found:
                            self.bus.pick_setrow(f[0], True)
                            self.bus.pick_setcol(f[1], True)
                            self.bus.pick.write_byte()
                            print("wrote found byte")
                            time.sleep(PREVIOUS_WAIT_TIME)
                            self.bus.pick_def()
                            time.sleep(DIGIT_CLEAR_TIME)
                        self.bus.pick_def()
                        self.bus.pick_setrow(r, True)
                        self.bus.pick_setcol(c, True)
                        self.bus.pick.write_byte()
                        #input("> start LED wait <")
                        if not self.wait_for_led():
                            print("LED not active, added digit '{}'".format(DIGIT_CONVERT[r][c]))
                            found.append((r, c))
                            self.logger.log("digit '{}' found at {},{}", DIGIT_CONVERT[r][c], r, c)
                            self.disp_digit(DIGIT_CONVERT[r][c])
                            found_digit = True
                            break
                        else:
                            print("LED was active")
                    if found_digit:
                        break
                if not found_digit:
                        print("Searched every digit and unable to find digit, aborting...")
                        self._do_loop = False
                if len(found) == PASSWORD_LENGTH:
                    pwd = ""
                    for f in found:
                        pwd += DIGIT_CONVERT[f[0]][f[1]]
                    print("Found password:", pwd)
                    self._do_loop = False

    def wait_for_led(self):
        # returns true if the LED turned on
        # False if it took too long
        self.led_timer.restart()
        self.led_wait_time_done = False
        if USE_INTERRUPT:
            self.led_waiter.wait()
            self.led_timer.reset()
            self.logger.logd("stopped waiting for LED, led timer finished: {}", self.led_wait_time_done)
            return not self.led_wait_time_done
        else:
            self.bus.pick.read_byte()
            while self.bus.pick_led == 1:
                if self.led_wait_time_done:
                    self.logger.logd("stopped waut for LED due to timer expiring")
                    return False
                time.sleep(0.010)
                self.bus.pick.read_byte()
                self.logger.logt("read byte, states: {}", list(self.bus.pick))
            self.led_timer.reset()
            self.logger.logd("stopped waiting for LED due to it being active")
            return True

    def led_timer_elapsed(self):
        self.led_wait_time_done = True
        if USE_INTERRUPT:
            self.led_waiter.clear()

    def interrupt_line_active(self):
        # the interrupt line handler
        self.led_waiter.clear()

    def disp_digit(self, digit):
        pass

    def cleanup(self):
        self.led_timer.cleanup()
