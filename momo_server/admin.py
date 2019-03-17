from django.contrib import admin

# Register your models here.
from momo_server.models import Sms, Operator, Station, Answer, Transaction, Proof, SmsSender

admin.site.register(Sms)
admin.site.register(SmsSender)
admin.site.register(Operator)
admin.site.register(Transaction)
admin.site.register(Answer)
admin.site.register(Station)
admin.site.register(Proof)

