from django.conf import settings
from django.db import models
from django.utils import timezone


class Result(models.Model):
    title = models.TextField()
    url = models.URLField(unique=True)


class Job(models.Model):
    class Status(models.TextChoices):
        SCRAPING = 'SCRAPING', 'Scraping'
        WAITING = 'WAITING', 'Waiting'

    scrape_interval_seconds = 60

    start_url = models.TextField(unique=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.WAITING
    )
    last_scraped = models.DateTimeField(
        null=True,
        blank=True
    )
    results = models.ManyToManyField(Result)

    def is_due(self):
        if self.last_scraped is None:
            return True
        seconds_since_last_scrape = (timezone.now() - self.last_scraped).seconds
        return seconds_since_last_scrape > settings.SCRAPE_INTERVAL_SECONDS

class Subscriber(models.Model):
    chat_id = models.CharField(max_length=100, unique=True)
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='subscribers'
    )
    seen_results = models.ManyToManyField(Result)

    @property
    def unseen_results(self):
        seen_result_ids = [result.id for result in self.seen_results.all()]
        return self.job.results.exclude(id__in=seen_result_ids)
