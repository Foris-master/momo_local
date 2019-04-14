import difflib
import glob
from pprint import pprint
import re
import sys
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
from time import sleep, time

import serial
from gsmmodem import GsmModem
from gsmmodem.exceptions import TimeoutException, CommandError

from momo_server.models import Transaction, Station
from pool.dbpool import update_stations
from pool.gsmpool import ModemDriver

BAUDRATE = 115200


class WsHandler:
    def describe(self):
        md = ModemDriver()
        res = update_stations(md.get_stations(self.response['data'], self.response['modem']['stations']))
        return {'command': self.command, 'data': res}

    def proceed_momo(self):
        md = ModemDriver()
        station = Station.objects.filter(imsi=self.response['data']['station']['imsi']).get()
        tid = self.response['transaction_id']
        if Transaction.objects.filter(track_id=tid).exists():
            trans = Transaction.objects.filter(track_id=tid).get()
        else:
            trans = Transaction()

        trans.amount = self.response['transaction']['amount']
        trans.track_id = self.response['transaction_id']
        trans.is_deposit = self.response['transaction']['is_deposit']
        trans.status = 'new'
        trans.recipient = self.response['transaction']['recipient']
        trans.user = self.response['transaction']['user']
        trans.mobile_wallet = self.response['transaction']['mobile_wallet']

        trans.save()

        results = md.proceed_momo(self.response['data'])
        if results['data']['status'] == 'close-ok':
            trans.status = 'pending'
            trans.save()
        else:
            trans.delete()

        # pprint(results)

        results = {
            'transaction_id': self.response['transaction_id'],
            'station_id': self.response['station_id'],
            'last_answer': results['data']['status'],
            'response': results['response']
        }
        return {'command': self.command, 'data': results}

    commands = {
        'describe': describe,
        'proceed_momo': proceed_momo,
    }

    def __init__(self, response):
        # pprint(response, width=1)
        self.response = response
        # self.modem = response['modem']
        # self.data = response['data']
        self.command = response['command']
        # self.operators = response['data'].keys()

    def proceed(self):
        return self.commands[self.command](self)
