import difflib
import json
from pprint import pprint
from time import time, ctime

from django_cron import CronJobBase, Schedule

from momo_server.models import Operator, Station, Sms, SmsSender, Transaction
from pool.dbpool import update_stations
from pool.gsmpool import ModemDriver


class FetchStationJob(CronJobBase):
    RUN_EVERY_MINS = 5  # every 5 minutes

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'momo_server.fetch_stations'  # a unique code

    def do(self):
        start = time()
        ops = Operator.objects.all()
        operators = {}
        imsis = []
        for operator in ops:
            operators[operator.tag] = {}
        md = ModemDriver()
        update_stations(md.get_stations(operators))
        finish = time()
        t = (finish - start)
        print('time ' + str(t))


class CollectSmsJob(CronJobBase):
    RUN_EVERY_MINS = 1  # every 5 minutes

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'momo_server.collect_sms'  # a unique code

    def do(self):
        start = time()

        if not Transaction.objects.filter(status='new').exists():

            stations = Station.objects.all()
            ports = []
            for station in stations:
                ports.append(station.port)

            md = ModemDriver()
            results = md.collect_sms(ports)
            for port, data in results.items():
                station = Station.objects.filter(port=port).get()
                for sender, texts in data.items():
                    if SmsSender.objects.filter(name=sender).exists():
                        s = SmsSender.objects.filter(name=sender).first()
                        # print(s.name, sender)
                    else:
                        s = SmsSender.objects.filter(name='unkown', operator_id=station.operator_id).get()
                    for sms in texts:
                        print("------------------------------------\r\n")
                        print("------------" + s.name + "------------------\r\n")
                        print(sms['text'] + "\r\n")
                        print("------------------------------------\r\n\r\n")
                        # received_at__date=sms['time'],
                        mt = {'sender_number': sms['number']}
                        ref = ','.join([str(r) for r in sms['references']])
                        olsms = Sms.objects.filter(sender_id=s.id, references=ref).first()
                        if olsms is not None:
                            olsms.content = olsms.content + sms['text']
                            olsms.save()
                        else:

                            if not Sms.objects.filter(sender_id=s.id, content=sms['text']).exists():

                                Sms.objects.create(
                                    content=sms['text'],
                                    references=ref,
                                    sender_id=s.id,
                                    station_id=station.id,
                                    received_at=sms["time"],
                                    metadata=json.dumps(mt)
                                )
                        
        finish = time()
        t = (finish - start)
        print('time ' + str(t), ctime())


class UpdateTransactionStatus(CronJobBase):
    RUN_EVERY_MINS = 5  # every 5 minutes

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'momo_server.fetch_stations'  # a unique code

    def do(self):
        start = time()
        md = ModemDriver()
        update_stations(md.get_stations())
        finish = time()
        t = (finish - start)
        print('time ' + str(t))
