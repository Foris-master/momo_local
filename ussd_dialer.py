#!/usr/bin/env python

"""\
Demo: Simple USSD example
Simple demo app that initiates a USSD session, reads the string response and closes the session
(if it wasn't closed by the network)
Note: for this to work, a valid USSD string for your network must be used.
"""

# from __future__ import print_function
from pprint import pprint
from time import time
import serial
from gsmmodem.exceptions import TimeoutException, CommandError, InvalidStateException
from gsmmodem.modem import GsmModem

# [{'COM10': 'Orange CAM'}, {'COM11': 'MTN CAM'}] no wallet 656851274  698126350 677004603
#  699508091  653560544 660867001
# {'/dev/ttyACM7':'MTN CAM'} {'/dev/ttyACM6':'Orange CAM'}
PORT = '/dev/ttyACM6'
BAUDRATE = 115200
# USSD_STRING = '*135*8#'
USSD_STRING = '#149#'
# USSD_STRING = '*126#'
PIN = None  # SIM card PIN (if any)

if __name__ == '__main__':
    start = time()
    modem = GsmModem(PORT, BAUDRATE)
    try:
        print(modem.alive)
        if modem.alive:
            raise CommandError
        modem.connect()
        modem.waitForNetworkCoverage(10)

    except CommandError as e:
        # print('DTMF playback failed: {0}'.format(e))
        modem.smsEncoding = "GSM"
        response = modem.sendUssd(USSD_STRING, responseTimeout=60)  # response type: gsmmodem.modem.Us
        msg = response.message
        answer = None
        try:

            while answer != 'stop':
                print(msg)
                answer = input('Reply ')
                if answer != 'stop':
                    response = response.reply(answer)
                    msg = response.message
        except TimeoutException as ex:
            print(ex)
    except (InvalidStateException) as ex:
        print(ex)
    except (OSError, serial.SerialException, TimeoutException) as ex:
        print(ex)
    finally:
        modem.close()

    finish = time()

    t = (finish - start)
    print('time saved by parallelizing: ' + str(t))
