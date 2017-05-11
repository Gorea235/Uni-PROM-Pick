#! /usr/bin/env python3
from bus_wrapper import BusWrapper
import time
import threading
from timeout import Timeout
import os

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
DIGIT_ID_TABLE = {}
for r in range(N_ROWS):
    for c in range(N_COLS):
        DIGIT_ID_TABLE[DIGIT_CONVERT[r][c]] = (r, c)
USE_INTERRUPT = False
INTERRUPT_GPIO = 17
PASSWORD_LENGTH = 4
LED_WAIT_TIME = 1
PREVIOUS_WAIT_TIME = 0.5
DIGIT_CLEAR_TIME = 1
BUS_SETTLE_TIME = 0.005

BRUTE_FORCE_PRESEARCH_LIST = "brute_force_search.dat"
DIGIT_DISP_CONVERT = {
    # d     0      1      2      3      4      5      6      7
    "0": [True,  True,  True,  False, True,  True,  True,  False],
    "1": [False, False, True,  False, True,  False, False, False],
    "2": [True,  True,  False, False, True,  True,  False, True],
    "3": [False, True,  True,  False, True,  True,  False, True],
    "4": [False, False, True,  False, True,  False, True,  True],
    "5": [True,  True,  False, False, False, True,  True,  True],
    "6": [True,  True,  True,  False, False, True,  True,  True],
    "7": [False, False, True,  False, True,  True,  False, False],
    "8": [True,  True,  True,  False, True,  True,  True,  True],
    "9": [False, True,  True,  False, True,  True,  True,  True],
    "*": [True,  False, True,  False, True,  False, True,  True],
    "#": [False, True,  False, False, False, True,  False, True]
}
DIGIT_TEST_WAIT_TIME = 1


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
        self.bus.pick_def()
        self.bus.pick.write_byte()
        self.disp_digit("#")
        time.sleep(DIGIT_TEST_WAIT_TIME)
        self.disp_digit("*")
        time.sleep(DIGIT_TEST_WAIT_TIME)
        for i in range(9, -1, -1):
            self.disp_digit(str(i))
            time.sleep(DIGIT_TEST_WAIT_TIME)
        self.disp_digit(None)
        input("Press enter to start the crack")
        if self.brute:
            search_list = []
            pwd_tbl = {}
            if os.path.isfile(BRUTE_FORCE_PRESEARCH_LIST):
                with open(BRUTE_FORCE_PRESEARCH_LIST) as f:
                    for l in f:
                        search_list.append(l.strip())
                        pwd_tbl[search_list[-1]] = True
            search_list += self.generate_password_list("", pwd_tbl)
            for pwd in search_list:
                for c in pwd:
                    self.bus.pick_def()
                    time.sleep(DIGIT_CLEAR_TIME)
                    self.bus.pick_def()
                    self.bus.pick_setrow(DIGIT_ID_TABLE[c][0])
                    self.bus.pick_setcol(DIGIT_ID_TABLE[c][1])
                    self.bus.write_byte()
                    time.sleep(PREVIOUS_WAIT_TIME)
                if not self.wait_for_led():
                    print("LED not active after password injection, correct one found")
                    print("Password found:", pwd)
                    return
                else:
                    self.logger.logd(
                        "Password {} caused LED to become active, moving to next password", pwd)
            print("Unable to find password")
        else:
            found = []
            while self._do_loop:
                # input("> do next loop <")
                found_digit = False
                for r in range(N_ROWS):
                    for c in range(N_COLS):
                        # input("> do next digit test ('{}')({},{}) <".format(DIGIT_CONVERT[r][c], r,c))
                        self.bus.pick_def()
                        time.sleep(DIGIT_CLEAR_TIME)
                        for f in found:
                            self.bus.pick_setrow(f[0], True)
                            self.bus.pick_setcol(f[1], True)
                            self.bus.pick.write_byte()
                            # print("wrote found byte")
                            time.sleep(PREVIOUS_WAIT_TIME)
                            self.bus.pick_def()
                            time.sleep(DIGIT_CLEAR_TIME)
                        self.bus.pick_def()
                        self.bus.pick_setrow(r, True)
                        self.bus.pick_setcol(c, True)
                        self.bus.pick.write_byte()
                        # input("> start LED wait <")
                        if not self.wait_for_led():
                            # print("LED not active, added digit '{}'".format(
                                # DIGIT_CONVERT[r][c]))
                            found.append((r, c))
                            self.logger.log(
                                "digit '{}' found at {},{}", DIGIT_CONVERT[r][c], r, c)
                            self.disp_digit(DIGIT_CONVERT[r][c])
                            found_digit = True
                            break
                        # else:
                            # print("LED was active")
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

    def generate_password_list(self, cpwd, pwd_tbl):
        if len(cpwd) == PASSWORD_LENGTH:
            if cpwd not in pwd_tbl:
                return [cpwd]
            else:
                return []
        pwds = []
        for k in DIGIT_ID_TABLE.keys():
            pwds += self.generate_password_list(cpwd + k, pwd_tbl)
        return pwds

    def wait_for_led(self):
        # returns true if the LED turned on
        # False if it took too long
        self.led_timer.restart()
        self.led_wait_time_done = False
        if USE_INTERRUPT:
            self.led_waiter.clear()
            self.led_waiter.wait()
            self.led_timer.reset()
            self.logger.logd(
                "stopped waiting for LED, led timer finished: {}", self.led_wait_time_done)
            return not self.led_wait_time_done
        else:
            self.bus.pick.write_byte()
            time.sleep(BUS_SETTLE_TIME)
            self.bus.pick.read_byte()
            while self.bus.pick_led == 1:
                if self.led_wait_time_done:
                    self.logger.logd(
                        "stopped waiting for LED due to timer expiring")
                    return False
                time.sleep(0.005)
                self.bus.pick.write_byte()
                time.sleep(BUS_SETTLE_TIME)
                self.bus.pick.read_byte()
                self.logger.logt("read byte, states: {}", list(self.bus.pick))
            self.led_timer.reset()
            self.logger.logd("stopped waiting for LED due to it being active")
            return True

    def led_timer_elapsed(self):
        self.led_wait_time_done = True
        if USE_INTERRUPT:
            self.led_waiter.set()

    def interrupt_line_active(self):
        # the interrupt line handler
        self.led_waiter.set()

    def disp_digit(self, digit):
        if digit is None:
            for i in len(self.bus.ddisp):
                self.bus.ddisp[i] = False
        else:
            for i in len(self.bus.ddisp):
                self.bus.ddisp[i] = DIGIT_DISP_CONVERT[i]
        self.bus.ddisp.write_byte()

    def cleanup(self):
        self.led_timer.cleanup()
