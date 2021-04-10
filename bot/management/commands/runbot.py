from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management import BaseCommand

from bot.bot import run_bot


class Command(BaseCommand):
    help = 'Runs the telegram bot'

    def handle(self, *args, **options):
        if not settings.TELEGRAM_API_TOKEN:
            raise ImproperlyConfigured('IMMOBOT_TELEGRAM_API_TOKEN not set')

        run_bot()
