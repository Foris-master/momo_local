import difflib

from momo_server.models import Operator, Station


def update_stations(results):
    print(results)
    ops = Operator.objects.all()
    operators = []
    imsis = []
    for operator in ops:
        operators.append(operator.tag)
    for (port, value) in results.items():
        nn = str(value['network'])
        imsis.append(value['imsi'])
        op = difflib.get_close_matches(nn.lower(), operators)[0]
        opid = Operator.objects.filter(tag=op).first().id
        old_station = Station.objects.filter(imei=value['imei']).first()
        if old_station is not None:
            old_station.imei = None
            old_station.save()
        old_station = Station.objects.filter(port=port).first()
        if old_station is not None:
            old_station.port = None
            old_station.save()

        if not Station.objects.filter(imsi=value['imsi']).exists():
            station = Station()
            station.state = 'free'
            station.name = value['imsi']
            station.imsi = value['imsi']
        else:
            station = Station.objects.filter(imsi=value['imsi']).first()
            # if 'balance' in dat and dat['balance']['value'] is not None:
            #     service = Service.objects.filter(tag=dat['balance']['service']).first()
            #     ss = ServiceStation.objects.filter(station=station, service=service).first()
            #     b = dat['balance']['value']
            #     b = b.replace(',', '')
            #     ss.balance = int(float(b))
            #     ss.save()
        station.phone_number = value['phone_number']
        station.imei = value['imei']
        station.operator_id = opid
        station.port = port
        station.save()
    Station.objects.exclude(imsi__in=imsis).update(state='offline')

    return  results
