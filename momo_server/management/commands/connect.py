import json
import os
from pprint import pprint

import requests
from django.core.management import BaseCommand, call_command
from requests.exceptions import ConnectionError
import websocket

from momo_server.consumers import WsHandler
from pool.gsmpool import ModemDriver

try:
    import thread
except ImportError:
    import _thread as thread
import time


class Command(BaseCommand):
    help = "DEV COMMAND: Fill databasse with a set of data for testing purposes"
    token = None

    def handle(self, *args, **options):
        websocket.enableTrace(True)
        try:
            if self.token is None:
                print('fetching new token')
                url = os.getenv('MOMO_TOKEN_SERVER_HTTP').format(client_id=os.getenv('CLIENT_ID'),
                                                                 client_secret=os.getenv('CLIENT_SECRET'))
                # url = url + 'oauth/token/'
                url = os.getenv('MOMO_SERVER_HTTP') + 'oauth/token/'
                r = requests.post(
                    url,
                    data={
                        'grant_type': 'client_credentials',
                        'client_id':os.getenv('CLIENT_ID'),
                        'client_secret':os.getenv('CLIENT_SECRET'),
                        'scope': 'read modem'
                    },
                )
                self.token = r.json()['access_token']
                with open('token_save.txt', 'w') as token_file:
                    token_file.write(self.token)
                    token_file.close()
                # print(r.json()['access_token'])

            ws = websocket.WebSocketApp(
                os.getenv('MOMO_SERVER_WS') + "ws/modem/{tag}/".format(tag=os.getenv('MODEM_TAG')),
                header={'Authorization: Bearer' + self.token},
                on_message=on_message,
                on_error=on_error,
                on_close=on_close)
            ws.on_open = on_open
            ws.run_forever()
        except ConnectionError as ex:
            print(ex)
        except Exception as ex:
            print(ex)


def on_message(ws, message):
    # print(message)
    message = json.loads(message)
    print('received command ' + message['command'])
    # md = ModemDriver(message)
    # res = md.proceed()
    wsh = WsHandler(message)
    res = wsh.proceed()
    pprint(res)
    ws.send(json.dumps(res))


def on_error(ws, error):
    print(error)


def on_close(ws):

    TPAUSE = 30
    print("### closed retry in " + str(TPAUSE) + " second ###")
    time.sleep(TPAUSE)
    TPAUSE *= 2
    call_command('connect')


def on_open(ws):
    def run(*args):
        # for i in range(10):
        #     time.sleep(1)
        #     ws.send("Hello %d" % i)
        # time.sleep(1)
        # ws.close()
        ws.send(json.dumps({'command': 'connected', 'msg': "Hello"}))
        print("modem connected !")

    thread.start_new_thread(run, ())
