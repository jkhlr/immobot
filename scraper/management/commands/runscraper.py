from time import sleep

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management import BaseCommand

from scraper.scraper import run_scraper, RateLimitException


class Command(BaseCommand):
    help = 'Runs the scraper'

    def handle(self, *args, **options):
        if not settings.SCRAPER_DEBUG and not settings.SPLASH_URL:
            raise ImproperlyConfigured('IMMOBOT_SPLASH_URL not set')

        run_scraper()
