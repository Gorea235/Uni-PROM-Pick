#! /usr/bin/env python3
from interface import Interface
from logger import Logger

BRUTE_FORCE = False
LOG_FILE = "events.log"


class App:
    def __init__(self):
        self.logger = Logger(LOG_FILE)
        self.iface = Interface(BRUTE_FORCE, self.logger)

        self.iface.crack_password()

        self.logger.cleanup()


if __name__ == "__main__":
    App()
