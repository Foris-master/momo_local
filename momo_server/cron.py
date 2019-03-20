import difflib
from pprint import pprint
from time import time

from django_cron import CronJobBase, Schedule

from momo_server.models import Operator, Station, Sms, SmsSender
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
                    print(s.name, sender)
                else:
                    s = SmsSender.objects.filter(name='unkown', operator_id=station.operator_id).get()
                for sms in texts:
                    mt = sms['number'] + ' at ' + str(sms["time"])
                    if not Sms.objects.filter(mt=mt, sender_id=s.id,content=sms['text']).exists():
                        Sms.objects.create(
                            content=sms['text'],
                            references=','.join([str(r) for r in sms['references']]),
                            sender_id=s.id,
                            station_id=station.id,
                            metadata=mt
                        )
        finish = time()
        t = (finish - start)
        print('time ' + str(t))


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
