import json
import os
import re

import requests
from django.db import models

# Create your models here.

from django.db import models
from django.db.models.signals import post_init, post_save
from django.dispatch import receiver

from momo_local.settings import BASE_DIR

STATION_STATES = [('free', 'FREE'), ('busy', 'BUSY'), ('offline', 'OFFLINE')]
SMS_TYPES = [('partial', 'PARTIAL'), ('whole', 'WHOLE')]
TRANSACTION_STATUSES = [('new', 'NEW'), ('pending', 'PENDING'), ('paid', 'PAID'), ('proven', 'PROVEN'),
                        ('cancel', 'CANCEL')]


class Operator(models.Model):
    name = models.CharField(max_length=100, blank=False)
    tag = models.CharField(unique=True, max_length=10)
    country = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('updated_at',)

    def __str__(self):
        return self.name


class Answer(models.Model):
    answer = models.CharField(max_length=20, blank=False)
    is_int = models.BooleanField(blank=False, default=False)
    order = models.IntegerField(blank=False)
    description = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('order',)

    def __str__(self):
        return self.answer


class Station(models.Model):
    name = models.CharField(max_length=100, blank=False)
    state = models.CharField(choices=STATION_STATES, default='offline', max_length=100)
    phone_number = models.CharField(unique=True, max_length=14, blank=True, null=True)
    imei = models.CharField(unique=True, max_length=20, null=True, blank=True)
    imsi = models.CharField(max_length=20, unique=True, blank=False)
    port = models.CharField(max_length=20, null=True, blank=True)
    operator = models.ForeignKey(Operator, on_delete=models.CASCADE, related_name='stations')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('updated_at',)

    def __str__(self):
        return self.name


class Transaction(models.Model):
    amount = models.IntegerField(blank=False)
    track_id = models.CharField(blank=False, unique=True, max_length=20)
    is_deposit = models.BooleanField(default=True)
    status = models.CharField(choices=TRANSACTION_STATUSES, default='new', max_length=100)
    recipient = models.CharField(max_length=14)
    user = models.IntegerField(blank=False)
    mobile_wallet = models.CharField(blank=False, max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('created_at',)

    def __str__(self):
        return str(self.amount) + ' FCFA ' + self.status


@receiver(post_save, sender=Transaction)
def proceed_transaction(sender, **kwargs):
    transaction = kwargs.get('instance')

    if kwargs.get('created') is False:
        if transaction.status == 'proven':
            try:

                proof = transaction.proof_set.first()
                url = os.getenv('MOMO_TOKEN_SERVER_HTTP').format(client_id=os.getenv('CLIENT_ID'),
                                                                 client_secret=os.getenv('CLIENT_SECRET'))
                # url = url + 'oauth/token/'
                url = os.getenv('MOMO_SERVER_HTTP') + 'api/v1/transaction/prove/'
                token_path = os.path.join(BASE_DIR, 'token_save.txt')
                with open(token_path, 'r') as token_file:
                    token = token_file.read()
                    token_file.close()
                if token is not None:
                    headers = {'Authorization': 'Bearer ' + token}
                    r = requests.post(
                        url,
                        data={
                            'transaction_id': transaction.track_id,
                            'amount': proof.amount,
                            'mno_id': proof.mno_id,
                            'mno_respond': proof.mno_respond,
                            'station': proof.station.imsi,
                            'metadata': proof.metadata
                        },
                        headers=headers
                    )
                    rep = r.json()
                    if 'status' in rep and rep['status'] == 'ok':
                        transaction.delete()

            except ConnectionError as ex:
                print(ex)
            except Exception as ex:
                print(ex)
    else:
        pass


class Proof(models.Model):
    amount = models.IntegerField(blank=False)
    mno_id = models.CharField(blank=False, max_length=100)
    metadata = models.CharField(blank=True, max_length=255)
    mno_respond = models.TextField()
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('updated_at',)

    def __str__(self):
        return str(self.amount)


class SmsSender(models.Model):
    operator = models.ForeignKey(Operator, on_delete=models.CASCADE, related_name='sms')
    name = models.TextField(blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('updated_at',)

    def __str__(self):
        return str(self.name)


class Sms(models.Model):
    content = models.TextField(blank=False)
    metadata = models.CharField(max_length=255, null=True)
    type = models.CharField(choices=SMS_TYPES, default='partial', max_length=25)
    references = models.TextField(blank=True, null=True)
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    sender = models.ForeignKey(SmsSender, on_delete=models.CASCADE)
    received_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('updated_at',)

    def __str__(self):
        return self.content[:20]


@receiver(post_save, sender=Sms)
def proceed_sms(sender, **kwargs):
    sms = kwargs.get('instance')

    if sms.type == 'whole':
        res = {}
        key = '([\{].+?[\}])'
        value = '(.+)'
        msg = sms.content
        for mask in sms.sender.smsmask_set.all():
            des = mask.content
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
                    res = None
            if type(res) is dict:
                mt = json.loads(sms.metadata)
                mt['new_balance'] = res['new_balance']
                a = res['amount']
                a = int(float(a))
                tel = res['phone_number']
                t = Transaction.objects.filter(recipient=tel, amount=a, status='pending').first()
                if t is not None:
                    p = Proof.objects.create(
                        amount=a,
                        mno_id=res['mno_id'],
                        mno_respond=msg,
                        station_id=sms.station_id,
                        transaction_id=t.id,
                        metadata=json.dumps(mt)
                    )
                    t.status = 'proven'
                    t.save()


class SmsMask(models.Model):
    content = models.TextField(blank=False)
    sender = models.ForeignKey(SmsSender, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('updated_at',)

    def __str__(self):
        return self.content[:20]
