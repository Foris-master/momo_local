from django.db import models

# Create your models here.

from django.db import models
from django.db.models.signals import post_init

STATION_STATES = [('free', 'FREE'), ('busy', 'BUSY'), ('offline', 'OFFLINE')]
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
    imsi = models.CharField(max_length=20, unique=True, blank=False )
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
        ordering = ('updated_at',)

    def __str__(self):
        return str(self.amount) + ' FCFA ' + self.status


class Proof(models.Model):
    amount = models.IntegerField(blank=False)
    mno_id = models.CharField(blank=False, max_length=100)
    mno_respond = models.CharField(blank=False, max_length=255)
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
    metadata = models.CharField(max_length=255,null=True)
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

class SmsMask(models.Model):
    content = models.TextField(blank=False)
    sender = models.ForeignKey(SmsSender, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('updated_at',)

    def __str__(self):
        return self.content[:20]
