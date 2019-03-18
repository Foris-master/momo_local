#!/usr/bin/env python

"""\
Demo: Simple USSD example
Simple demo app that initiates a USSD session, reads the string response and closes the session
(if it wasn't closed by the network)
Note: for this to work, a valid USSD string for your network must be used.
"""

import glob
# from __future__ import print_function
import sys

import serial
import serial.tools.list_ports
from gsmmodem import GsmModem
from gsmmodem.exceptions import CommandError, TimeoutException

PORT = 'COM18'
BAUDRATE = 115200
USSD_STRING = '#149#'
PIN = None  # SIM card PIN (if any)


def available_ports2():
    aports = []
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            aports.append(port)
        except (OSError, serial.SerialException):
            pass

    return aports


def available_ports():
    myports = [tuple(p) for p in list(serial.tools.list_ports.comports())]
    return [p[0] for p in myports if 'location=' in p[2].lower()]


def enabled_ports(aports):
    eports = []
    for port in aports:
        modem = GsmModem(port, BAUDRATE)
        try:
            modem.connect()
            print(modem.supportedCommands)

        except (CommandError) as e:
            # print('DTMF playback failed: {0}'.format(e))
            eports.append({port: modem.networkName})

        except (OSError, serial.SerialException, TimeoutException):
            pass
        finally:
            modem.close()
    return eports


if __name__ == '__main__':
    print(enabled_ports(available_ports()))
