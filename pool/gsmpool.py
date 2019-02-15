#!/usr/bin/env python

"""\
Demo: Simple USSD example
Simple demo app that initiates a USSD session, reads the string response and closes the session
(if it wasn't closed by the network)
Note: for this to work, a valid USSD string for your network must be used.
"""

# from __future__ import print_function
import difflib
import glob
import pprint
import re
import sys
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
from time import sleep, time

import serial
from gsmmodem.exceptions import TimeoutException, CommandError

PORT = 'COM18'
BAUDRATE = 115200
USSD_STRING = '#149#'
PIN = None  # SIM card PIN (if any)

from gsmmodem.modem import GsmModem


class ModemDriver:
    def describe(self):
        start = time()

        self.stations = self.modem['stations']
        results = self.available_ports()
        results = self.get_states(results)
        enabled_port = {k: v for (k, v) in results.items() if v['enabled']}
        results = self.get_infos(enabled_port)
        finish = time()
        t = (finish - start)
        print('modem answered to ' + self.command)
        return {'command': self.command, 'data': results}

    def proceed_momo(self):
        start = time()
        station = self.data['station']
        service = self.data['service']
        results = {}
        modem = GsmModem(station['port'], BAUDRATE)
        try:
            modem.connect()
            modem.waitForNetworkCoverage(10)

        except CommandError as e:
            # print('DTMF playback failed: {0}'.format(e))
            results = self.process_ussd(modem, service['ussd'], service['answers'])

        except (OSError, serial.SerialException, TimeoutException) as ex:
            print(ex)
        finally:
            modem.close()

        # return {port: result}
        results = {
            'transaction_id': self.response['transaction_id'],
            'station_id': self.response['station_id'],
            'response': results['response']
        }
        finish = time()
        t = (finish - start)
        print('modem answered to ' + self.command)
        return {'command': self.command, 'data': results}

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

    def available_ports(self):
        """ Lists serial port names

                :raises EnvironmentError:
                    On unsupported or unknown platforms
                :returns:
                    A list of the serial ports available on the system
            """
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        futures = []

        pool = ThreadPoolExecutor()

        for port in ports:
            futures.append(pool.submit(self.check, port))

        wait(result, return_when=ALL_COMPLETED)
        for future in futures:
            if future.result() is not None:
                result.append(future.result())
        return result

    def get_state(self, port):
        modem = GsmModem(port, BAUDRATE)
        result = {}
        try:
            modem.connect()
            print(modem.supportedCommands)

        except (CommandError) as e:
            # print('DTMF playback failed: {0}'.format(e))
            result['enabled'] = True

        except (OSError, serial.SerialException, TimeoutException):
            result['enabled'] = False
            pass
        finally:
            modem.close()
        return {port: result}

    def process_ussd(self, modem, code, answers):
        modem.smsEncoding = "GSM"
        response = modem.sendUssd(code, responseTimeout=30)  # response type: gsmmodem.modem.Us
        msg = response.message
        key = '([\{].+?[\}])'
        value = '(.+)'
        res = {}
        # print(msg)
        for answer in answers:
            a = answer['answer']
            if a == 'close':
                response.cancel()
            else:
                if answer['is_int']:
                    a = int(a)
                response = self.reply(response, a)
                msg = response.message
            if answer['description'] is not None and answer['description'].lower() != 'ras':
                des = answer['description']
                keys = re.findall(key, des, re.DOTALL)
                if keys:
                    for k in keys:
                        des = des.replace(k, value)
                    # msg= re.compile(r'[\n\r\t]').sub(' ',msg)
                    values = re.findall(des, msg)
                    if values:
                        if type(values[0]) is tuple:
                            values = values[0]
                        for i, v in enumerate(values):
                            k = keys[i].replace(' ', '')
                            k = k.replace('{', '')
                            k = k.replace('}', '')
                            res[k] = v
                        # print(res)
                        return res

        if 'transaction identique' in response.message:
            response = self.reply(response, 1)
            msg = response.message
        # print(msg)
        # phone = re.findall(r'\b\d+\b', msg)
        # re.findall(r'\d+', response.message)
        response.cancel()
        # if len(phone) == 1:
        #     return phone[0]
        # else:
        return {'response': msg}

    def get_info(self, port):
        result = {}
        modem = GsmModem(port, BAUDRATE)
        try:
            modem.connect()
            modem.waitForNetworkCoverage(10)

        except CommandError as e:
            # print('DTMF playback failed: {0}'.format(e))
            net = str(modem.networkName).lower()
            op = difflib.get_close_matches(net, self.operators)
            op = op[0]
            services = self.data[op]['services']
            balance, phone_number = None, None
            if 'phn' in services:
                phn_service = services['phn']
                phone_number = self.process_ussd(modem, phn_service['ussd'], phn_service['answers'])['number']
            if 'bal' in services:
                bal_service = services['bal']
                station = list(filter(lambda station: station['phone_number'] == phone_number, self.stations))
                if len(station) == 1 and 'service_stations' in station[0] \
                        and len(station[0]['service_stations']) == 1 \
                        and station[0]['service_stations'][0]['pin'] is not None:
                    answer = next(
                        (index for (index, d) in enumerate(bal_service['answers']) if d["answer"] == "{pin}"),
                        None)

                    if answer is not None:
                        bal_service['answers'][answer]['answer'] = station[0]['service_stations'][0]['pin']
                        balance = self.process_ussd(modem, bal_service['ussd'], bal_service['answers'])

            try:

                result['imei'] = modem.imei
                result['signal'] = modem.signalStrength
                result['network'] = modem.networkName
                result['alive'] = modem.alive
                result['imsi'] = modem.imsi
                result['manufacturer'] = modem.manufacturer
                result['model'] = modem.model
                result['operator'] = op
                result['phone_number'] = phone_number
                # result['description'] = str(balance)
                result['balance'] = {'value': balance['balance'], 'service': 'bal'}

            except Exception as e:
                print(str(e) + ' ligne 236')

        except (OSError, serial.SerialException, TimeoutException):
            pass
        finally:
            modem.close()
        return {port: result}

    def get_states(self, ports):
        results = {}

        futures = []

        pool = ThreadPoolExecutor()

        for port in ports:
            futures.append(pool.submit(self.get_state, port))

        wait(futures, return_when=ALL_COMPLETED)

        for future in futures:
            if type(future.result()) is dict:
                results.update(future.result())

        return results

    def get_infos(self, ports):
        # for port, val in ports.items():
        results = {}

        futures = []

        pool = ThreadPoolExecutor()

        for port in ports:
            futures.append(pool.submit(self.get_info, port))

        wait(futures, return_when=ALL_COMPLETED)

        for future in futures:
            if type(future.result()) is dict:
                results.update(future.result())
        return results

    def reply(self, response, choice):
        sleep(1)
        if response.sessionActive:

            # At this point, you could also reply to the USSD message by using response.reply()
            rep = response.reply(message=choice)
            # print('USSD reply received: {0}'.format(rep.message))
            return rep
        else:
            print('USSD session was ended by network.')
            response.cancel()
            return None

    def check(self, port):
        try:
            s = serial.Serial(port)
            s.close()
            return port
        except (OSError, serial.SerialException):
            pass

    def handleSms(self, sms):
        print(
            u'== SMS message received ==\nFrom: {0}\nTime: {1}\nMessage:\n{2}\n'.format(sms.number, sms.time, sms.text))
        print('Replying to SMS...')
        sms.reply(u'SMS received: "{0}{1}"'.format(sms.text[:20], '...' if len(sms.text) > 20 else ''))
        print('SMS sent.\n')

    def wait_sms(self, modem):
        modem = GsmModem(PORT, BAUDRATE, smsReceivedCallbackFunc=self.handleSms)

        modem.smsReceivedCallback = self.handleSms
        try:
            modem.rxThread.join(
                2 ** 31)  # Specify a (huge) timeout so that it essentially blocks indefinitely, but still receives CTRL+C interrupt signal
        finally:
            modem.close()


def get_phone_number(modem, op):
    # print('sms encode {0}'.format(modem.smsSupportedEncoding))
    if ('orange' in op.lower()):
        code = '#99#'
    elif ('mtn' in op.lower()):
        code = '*135*8#'
    else:
        return
    modem.smsEncoding = "GSM"
    response = modem.sendUssd(code, responseTimeout=30)  # response type: gsmmodem.modem.Us

    phone = re.findall(r'\b\d+\b', response.message)
    # re.findall(r'\d+', response.message)
    response.cancel()
    if len(phone) == 1:
        return phone[0]


def get_balance(modem, op):
    modem.smsEncoding = "GSM"
    if ('orange' in op.lower()):
        code = '#149#'
        response = modem.sendUssd(code, responseTimeout=30)  # response type: gsmmodem.modem.Us
        # response = reply(response, 6)
        # response = reply(response, 2)
        # response = reply(response, 2010)
    elif ('mtn' in op.lower()):
        code = '*126#'
        response = modem.sendUssd(code, responseTimeout=30)  # response type: gsmmodem.modem.Us
        # response = reply(response, 6)
        # response = reply(response, 1)
        # response = reply(response, 19850)

    else:
        return 0

    balance = re.findall("[-+]?\d+[\.,]?\d+|\d+", response.message)
    print('USSD reply received: {0}'.format(response.message))
    print(balance)
    if len(balance) == 1:
        return balance[0]
