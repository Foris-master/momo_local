import difflib
from time import time

from django_cron import CronJobBase, Schedule

from momo_server.models import Operator
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
            operators[operator.tag]={}
        md = ModemDriver()
        update_stations(md.get_stations(operators))
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
