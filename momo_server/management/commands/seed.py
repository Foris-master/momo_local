import json
import os

from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
    help = "DEV COMMAND: Fill databasse with a set of data for testing purposes"

    def handle(self, *args, **options):
        call_command('flush', '--noinput')
        call_command('loaddata', 'operators', 'sms_senders', 'sms_masks')
        # Fix the passwords of fixtures
