FROM python:3.9-alpine
RUN apk add bash python3-dev build-base linux-headers pcre-dev mariadb-connector-c-dev openssl-dev libffi-dev git
RUN pip install uwsgi

WORKDIR /etc/app
COPY ./requirements.txt ./
RUN pip install regex==2021.11.2
RUN pip install -r requirements.txt

COPY ./ ./

RUN DJANGO_SETTINGS_MODULE=settings.prod_without_db SECRET_KEY="ThEmUsTSecretKEYforBUILDstage123" TELEGRAM_TOKEN="0000000000:XXXXXXXXXXXXXXXXXXXXXXXXXXXX-XXXXXX" SLACK_CLIENT_OAUTH_ID=1 python manage.py collectstatic --no-input
RUN rm db.sqlite3

# This is required for prometheus_client to sync between uwsgi workers
RUN mkdir -p /tmp/prometheus_django_metrics;
RUN chown -R 1000:2000 /tmp/prometheus_django_metrics
ENV prometheus_multiproc_dir "/tmp/prometheus_django_metrics"

CMD [ "uwsgi", "--ini", "uwsgi.ini" ]
