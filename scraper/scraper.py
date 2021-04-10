import json
import logging
import signal
import threading
import time

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.utils import timezone

from database.models import Result, Job

JOB_POLL_PAUSE_SECONDS = 10

logger = logging.getLogger(__name__)


class SignalInterrrupt(Exception):
    pass


def run_scraper():
    def signal_handler(sig, frame):
        raise SignalInterrrupt(signal.Signals(sig).name)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGABRT, signal_handler)
    scraper = Scraper()
    logger.debug('Starting scraper...')
    scraper.start()
    logger.debug('Scaper started.')

    try:
        signal.pause()
    except SignalInterrrupt as e:
        logger.debug(f'Received {e}, Shutting down...')
        scraper.stop()


class RateLimitException(Exception):
    pass


class Scraper(threading.Thread):
    def __init__(self, pause_seconds=JOB_POLL_PAUSE_SECONDS):
        super().__init__()
        self._pause_seconds = pause_seconds
        self._running = False
        self._rate_limit_reached = False

    def run(self):
        self._running = True
        while self._running:
            time.sleep(self._pause_seconds)
            logger.debug('Checking for due jobs...')
            for job in Job.objects.filter(subscribers__isnull=False):
                if job.is_due():
                    logger.debug(f'Job {job.id} is due. Scraping...')
                    self.run_job(job)
                    logger.debug(f'Job {job.id} done!')
                if self._rate_limit_reached:
                    logger.debug('RateLimitException: sleeping for 1h...')
                    seconds_slept = 0
                    while seconds_slept < 60*60:
                        seconds_slept += 10
                        time.sleep(10)
                        self._rate_limit_reached = False


    def run_job(self, job):
        job.status = Job.Status.SCRAPING
        job.save()

        for item in self.get_items(job.start_url):
            try:
                item = Result.objects.get(url=item.url)
                item.title = item.title
                item.save()
            except Result.DoesNotExist:
                item = Result.objects.create(url=item.url, title=item.title)
            job.results.add(item)

        job.last_scraped = timezone.now()
        job.status = Job.Status.WAITING
        job.save()

    def get_items(self, url, debug=settings.SCRAPER_DEBUG):
        if debug:
            logger.debug('Debug mode: Scraping from file...')
            with open('scraper/output.html') as f:
                return [Result(**item) for item in self.parse_html(f.read())]

        items = []
        next_page_url = url
        while next_page_url and not self._rate_limit_reached:
            logger.debug(
                f'Pausing before request for '
                f'{settings.REQUEST_PAUSE_SECONDS}s...'
            )
            time.sleep(settings.REQUEST_PAUSE_SECONDS)
            html = self.fetch_url(next_page_url)
            if self._rate_limit_reached:
                continue
            for item in self.parse_html(html):
                items.append(Result(**item))
            next_page_url = self.get_next_page_url(html)
            logger.debug(f'Next page: {next_page_url}')
        return items

    def stop(self):
        if self._running:
            self._running = False
            self.join()

    def fetch_url(self, url):
        req_url = f"{settings.SPLASH_URL}/render.html"
        body = json.dumps({"url": url, "har": 1, "html": 0})
        headers = {'Content-Type': 'application/json'}
        content = requests.post(
            req_url,
            data=body,
            headers=headers
        ).content.decode()
        if 'Ich bin kein Roboter' in content:
            self._rate_limit_reached = True
        return content

    @staticmethod
    def parse_html(html):
        bs = BeautifulSoup(html, features='html.parser')
        links = bs.find_all(
            name='a',
            attrs={'class': 'result-list-entry__brand-title-container'}
        )
        exposes = []
        for link in links:
            if 'data-go-to-expose-id' in link.attrs:
                url = (
                    f"http://immobilienscout24.de/expose/"
                    f"{link['data-go-to-expose-id']}"
                )
                title = ' '.join(link.text.split())
                if title.startswith('NEU'):
                    title = title[3:]
                exposes.append({'title': title, 'url': url})
        return exposes

    @staticmethod
    def get_next_page_url(html):
        bs = BeautifulSoup(html, features='html.parser')
        links = bs.find_all('a')
        for link in links:
            if 'data-nav-next-page' in link.attrs:
                return f"http://immobilienscout24.de{link.attrs['href']}"
