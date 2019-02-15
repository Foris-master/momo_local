from django.contrib import admin

# Register your models here.
from momo_server.models import SMS, Operator, Station, Answer, Transaction, Proof

admin.site.register(SMS)
admin.site.register(Operator)
admin.site.register(Transaction)
admin.site.register(Answer)
admin.site.register(Station)
admin.site.register(Proof)

