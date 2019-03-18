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
import traceback
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
from time import sleep, time

import serial
from gsmmodem.exceptions import TimeoutException, CommandError

from momo_server.models import Operator, Station

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

    def get_sms(self):
        start = time()

        results = self.available_ports()
        results = self.get_states(results)
        enabled_port = {k: v for (k, v) in results.items() if v['enabled']}
        results = self.collect_sms(enabled_port)
        finish = time()
        t = (finish - start)
        print('modem answered to ' + self.command)
        return {'command': self.command, 'data': results}

    def proceed_momo(self, data):
        station = data['station']
        service = data['service']
        results = {}
        modem = GsmModem(station['port'], BAUDRATE)
        try:
            modem.connect()
            modem.waitForNetworkCoverage(10)

        except CommandError as e:
            # print('DTMF playback failed: {0}'.format(e))
            results = self.process_ussd(modem, service['ussd'], service['answer'])

        except (OSError, serial.SerialException, TimeoutException) as ex:
            print(ex)
        finally:
            modem.close()

        # return {port: result}

        return results

    commands = {
        'describe': describe,
        'proceed_momo': proceed_momo,
    }

    # def __init__(self):
    # pprint.pprint(response, width=1)
    # self.response = response
    # self.modem = response['modem']
    # self.data = response['data']
    # self.command = response['command']

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

        response = modem.sendUssd(code, responseTimeout=90)  # response type: gsmmodem.modem.Us

        tmp_answer = answers
        while True:
            rep = self.make_reply(response, tmp_answer)
            if rep['status'] != 'success':
                break
            response = rep['response']
            tmp_answer = rep['answer']

            if type(tmp_answer) is not dict:
                break
        data = rep['data']
        response.cancel()

        return {'status': rep['status'], 'response': response.message, 'data': data}

    def process_ussd_old(self, modem, code, answers):
        modem.smsEncoding = "GSM"
        response = modem.sendUssd(code, responseTimeout=30)  # response type: gsmmodem.modem.Us
        msg = response.message
        key = '([\{].+?[\}])'
        value = '(.+)'
        res = {}

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

    def get_info(self, port, services=None, stations=None):

        result = {}
        modem = GsmModem(port, BAUDRATE)
        try:
            modem.connect()
            modem.waitForNetworkCoverage(10)

        except CommandError as e:
            # print('DTMF playback failed: {0}'.format(e))
            net = str(modem.networkName).lower()
            op = difflib.get_close_matches(net, services.keys())
            op = op[0]

            if op in services and 'services' in services[op]:
                services = services[op]['services']

            balance, phone_number = None, None

            if services is not None and 'phn' in services:
                phn_service = services['phn']
                rep = self.process_ussd(modem, phn_service['ussd'], phn_service['answer'])  # ['number']
                if rep['status'] == 'success':
                    phone_number = rep['data']["number"]

            if services is not None and 'bal' in services:
                bal_service = services['bal']
                station = list(filter(lambda station: station['phone_number'] == phone_number, stations))
                if len(station) == 1 and 'service_stations' in station[0] \
                        and len(station[0]['service_stations']) == 1 \
                        and station[0]['service_stations'][0]['pin'] is not None:
                    bal_service['answer'] = self.fill_params(bal_service['answer'],
                                                             {'pin': station[0]['service_stations'][0]['pin']})
                    balance = self.process_ussd(modem, bal_service['ussd'], bal_service['answer'])
                    balance = balance['data']

                    # answer = next(
                    #     (index for (index, d) in enumerate(bal_service['answer']) if d["answer"] == "{pin}"),
                    #     None)
                    #
                    # if answer is not None:
                    #     bal_service['answers'][answer]['answer'] = station[0]['service_stations'][0]['pin']
                    #     balance = self.process_ussd(modem, bal_service['ussd'], bal_service['answer'])

            try:

                result['imei'] = modem.imei
                result['signal'] = modem.signalStrength
                result['network'] = modem.networkName
                result['alive'] = modem.alive
                result['imsi'] = modem.imsi
                result['manufacturer'] = modem.manufacturer
                result['model'] = modem.model
                result['network'] = modem.networkName
                result['operator'] = op
                result['phone_number'] = phone_number
                if balance is not None:
                    result['description'] = str(balance)
                    result['balance'] = {'value': balance['balance'], 'service': 'bal'}

            except Exception as e:
                print(str(e) + ' ligne 236')
                # traceback.print_exc()

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

    def get_infos(self, ports, services=None, stations=None):
        # for port, val in ports.items():
        results = {}

        futures = []

        pool = ThreadPoolExecutor()

        for port in ports:
            futures.append(pool.submit(self.get_info, port, services, stations))

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

    def collect_station_sms(self, port):
        results = {}
        modem = GsmModem(port, BAUDRATE)
        try:
            modem.connect()
            modem.waitForNetworkCoverage(10)

        except CommandError as e:
            # print('DTMF playback failed: {0}'.format(e))
            # net = str(modem.networkName).lower()

            # try:
            # memory can SM (sim) ME ( device storage) or MT for all
            for sms in modem.listStoredSms(delete=False):
                is_next = False
                tmp = {
                    'index': sms.index,
                    'number': sms.number,
                    'text': sms.text,
                    'time': sms.time,
                    'references': []
                }

                if sms.number in results:
                    for udh in sms.udh:
                        ind = next((index for (index, item) in enumerate(results[sms.number]) if
                                    udh.reference in item["references"]), None)
                        if ind:
                            is_next = True
                            results[sms.number][ind]['text'] = results[sms.number][ind]['text'] + sms.text
                        else:
                            tmp['references'].append(udh.reference)
                    if not is_next:
                        results[sms.number].append(
                            tmp
                        )
                else:
                    for udh in sms.udh:
                        tmp['references'].append(udh.reference)
                    results[sms.number] = [tmp]




        # except Exception as e:
        #     print(str(e) + ' ligne 236')

        except (OSError, serial.SerialException, TimeoutException):
            pass
        finally:
            modem.close()
        return {port: results}

    def collect_sms(self, ports):
        results = {}

        futures = []

        pool = ThreadPoolExecutor()

        for port in ports:
            futures.append(pool.submit(self.collect_station_sms, port))

        wait(futures, return_when=ALL_COMPLETED)

        for future in futures:
            if type(future.result()) is dict:
                results.update(future.result())
        return results

    def get_stations(self, data=None, stations=None):

        results = self.available_ports()
        results = self.get_states(results)
        enabled_port = {k: v for (k, v) in results.items() if v['enabled']}
        results = self.get_infos(enabled_port, data, stations)
        return results

    def fill_params(self, trees, data, res=None):
        if res is None:
            res = {}
        for key, val in trees.items():
            if type(val) is list:
                if key not in res:
                    res[key] = []
                for i, val2 in enumerate(val):
                    res[key].append(self.fill_params(val2, data, {}))
            else:
                found = False
                for key2, val2 in data.items():
                    if '{' + key2 + '}' == val:
                        res[key] = val2
                        found = True

                if not found:
                    res[key] = val
        return res

    def make_reply(self, response, answer):
        res = {}
        key = '([\{].+?[\}])'
        value = '(.+)'
        msg = response.message
        a = answer['answer']
        if type(a) is str and a.startswith('close'):
            response.cancel()
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
                    else:
                        res = des
                else:
                    res = {'description': res, 'status': a}
            else:
                res = None
        else:
            if answer['is_int']:
                a = int(a)

            try:
                response = self.reply(response, a)
            except TimeoutException as ex:
                return {'status': 'failed', 'msg': 'timeout reached'}
            except Exception as ex:
                return {'status': 'failed', 'msg': str(ex)}

        if 'next_answers' not in answer or len(answer['next_answers']) == 0:
            if type(res) is dict:
                return {'status': 'success', 'data': res, 'msg': 'stop', 'response': response, 'answer': 'close'}
            else:
                return {'status': 'failed', 'data': res, 'msg': 'stop', 'response': response, 'answer': 'close'}
        elif len(answer['next_answers']) == 1:
            # return response, answer['next_answers'][0]
            return {'status': 'success', 'data': None, 'response': response, 'answer': answer['next_answers'][0]}
        else:
            tab_des = [item['description'].lower() for item in answer['next_answers']]
            tt = difflib.get_close_matches(response.message.lower(), tab_des)
            return {'status': 'success', 'data': None, 'response': response,
                    'answer': answer['next_answers'][tab_des.index(tt[0])]}
