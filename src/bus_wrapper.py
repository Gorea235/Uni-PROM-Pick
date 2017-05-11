#! /usr/bin/env python3
import smbus
import time

BYTE_LENGTH = 8
HARDWARE_WAIT = 0.010 # 10ms


class _BusAddrWrapper:
    def __init__(self, addr, bus):
        self._addr = addr
        self._values = [False for _ in range(BYTE_LENGTH)]
        self._bus = bus

    def __getitem__(self, i):
        return self._values[i]

    def __setitem__(self, i, value):
        assert 0 <= i < BYTE_LENGTH
        assert isinstance(value, bool)
        self._values[i] = value

    def __len__(self):
        return BYTE_LENGTH

    def write_byte(self):
        wb = 0
        for i in range(BYTE_LENGTH):
            wb |= int(self._values[i]) << i
        self._bus.write_byte(self._addr, wb)
        time.sleep(HARDWARE_WAIT)

    def read_byte(self):
        rb = self._bus.read_byte(self._addr)
        for i in range(BYTE_LENGTH):
            self._values[i] = bool((1 << i) & rb)


class BusWrapper:
    def __init__(self, n):
        self._bus = smbus.SMBus(n)
        self._addrs = {}

    def add_addr(self, key, addr):
        assert key not in self._addrs
        self._addrs[key] = _BusAddrWrapper(addr, self._bus)

    def __getitem__(self, k):
        return self._addrs[k]
