import json
import os

from django.contrib.auth.models import User
from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
    help = "DEV COMMAND: Fill databasse with a set of data for testing purposes"

    def handle(self, *args, **options):
        call_command('flush', '--noinput')
        call_command('loaddata', 'users')
        # Fix the passwords of fixtures
        for user in User.objects.all():
            user.set_password(user.password)
            user.save()
        call_command('loaddata', 'operators', 'sms_senders', 'sms_masks')
        # Fix the passwords of fixtures
