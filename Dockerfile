FROM python:3.8-alpine as app

RUN apk add --no-cache tini gcc musl-dev libffi-dev libressl-dev

ENV BASE_DIR=/var/app
WORKDIR $BASE_DIR
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY manage.py manage.py
COPY immobot immobot
COPY database database
COPY bot bot
COPY scraper scraper

ENTRYPOINT ["/sbin/tini", "--"]


FROM app as web

ENV DJANGO_STATIC_ROOT=$BASE_DIR/static
RUN mkdir $DJANGO_STATIC_ROOT
RUN DJANGO_COLLECTSTATIC=1 python manage.py collectstatic --noinput

EXPOSE 8000
CMD ./manage.py migrate \
    && gunicorn immobot.wsgi \
        --name immobot \
        --bind 0.0.0.0:8000 \
        --workers 3 \
        --log-level=debug \
        --access-logfile - \
        --error-logfile -

FROM app as shell

ENTRYPOINT ["/sbin/tini", "--", "python", "manage.py"]
CMD shell
