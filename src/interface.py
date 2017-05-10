#! /usr/bin/env python3
from bus_wrapper import BusWrapper

BUS_ID = 1
BUS_ADDR_PICK = 0x38
BUS_ADDR_DDISP = 0x01  # ????


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

    @property
    def ddisp(self):
        return self._buswrap[self._ddisp_id]


class Interface:
    def __init__(self, brute_force, logger):
        self.logger = logger

        self.bus = BusAccessor()
        self.brute = brute_force

    def crack_password(self):
        pass
