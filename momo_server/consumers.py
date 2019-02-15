import difflib
import glob
import pprint
import re
import sys
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
from time import sleep, time

import serial
from gsmmodem import GsmModem
from gsmmodem.exceptions import TimeoutException, CommandError

from momo_server.models import Transaction
from pool.gsmpool import ModemDriver

BAUDRATE = 115200


class WsHandler:
    def describe(self):
        md = ModemDriver(self.response)
        return md.proceed()

    def proceed_momo(self):
        md = ModemDriver(self.response)
        return md.proceed()

    commands = {
        'describe': describe,
        'proceed_momo': proceed_momo,
    }

    def __init__(self, response):
        # pprint.pprint(response, width=1)
        self.response = response
        self.modem = response['modem']
        self.data = response['data']
        self.command = response['command']
        self.operators = response['data'].keys()

    def proceed(self):
        return self.commands[self.command](self)
