#!/usr/bin/env python
import logging
import threading
import time

from django.conf import settings
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Enable logging
from database.models import Subscriber, Job

NOTIFICATION_PAUSE_SECONDS = 1

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def watch(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat.id
    if len(update.message.text.split()) != 2:
        update.message.reply_text(f'Usage: /watch URL')
        return

    url = update.message.text.split()[1]
    job, _ = Job.objects.get_or_create(start_url=url)
    try:
        subscriber = Subscriber.objects.get(chat_id=chat_id)
        subscriber.job = job
    except Subscriber.DoesNotExist:
        subscriber = Subscriber(chat_id=chat_id, job=job)
    subscriber.save()

    update.message.reply_text(f'Subscribed to job {job.id}')


def stop(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat.id
    try:
        subscriber = Subscriber.objects.get(chat_id=chat_id)
        job_id = subscriber.job.id
        subscriber.delete()
        update.message.reply_text(
            f'Subscription to job {job_id} stopped'
        )
    except Subscriber.DoesNotExist:
        update.message.reply_text('No subscription to stop')


def run_bot():
    updater = Updater(settings.TELEGRAM_API_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('watch', watch))
    dispatcher.add_handler(CommandHandler('stop', stop))

    result_updater = ResultUpdater(updater)
    result_updater.start()
    updater.start_polling()

    updater.idle()
    result_updater.stop()


class ResultUpdater(threading.Thread):
    def __init__(self, updater, pause_seconds=NOTIFICATION_PAUSE_SECONDS):
        super().__init__()
        self._updater = updater
        self._pause_seconds = pause_seconds
        self._running = False

    def run(self):
        self._running = True
        while self._running:
            time.sleep(self._pause_seconds)
            self.send_result_updates()

    def send_result_updates(self):
        for subscriber in Subscriber.objects.all():
            for result in subscriber.unseen_results.all():
                self._updater.bot.send_message(
                    chat_id=subscriber.chat_id,
                    text=f"<a href=\"{result.url}\">{result.title}</a>",
                    parse_mode='HTML'
                )
                subscriber.seen_results.add(result)

    def stop(self):
        if self._running:
            self._running = False
            self.join()
