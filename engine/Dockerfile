FROM python:3.9-alpine3.16 AS base
RUN apk add bash python3-dev build-base linux-headers pcre-dev mariadb-connector-c-dev openssl-dev libffi-dev git

WORKDIR /etc/app
COPY ./requirements.txt ./
RUN pip install -r requirements.txt

# we intentionally have two COPY commands, this is to have the requirements.txt in a separate build step
# which only invalidates when the requirements.txt actually changes. This avoids having to unneccasrily reinstall deps (which is time-consuming)
# https://stackoverflow.com/questions/34398632/docker-how-to-run-pip-requirements-txt-only-if-there-was-a-change/34399661#34399661
COPY ./ ./

# Collect static files and create an SQLite database
RUN mkdir -p /var/lib/oncall
RUN DJANGO_SETTINGS_MODULE=settings.prod_without_db DATABASE_TYPE=sqlite3 DATABASE_NAME=/var/lib/oncall/oncall.db SECRET_KEY="ThEmUsTSecretKEYforBUILDstage123" python manage.py collectstatic --no-input
RUN chown -R 1000:2000 /var/lib/oncall

FROM base AS dev

# these are needed for the django dbshell command
RUN apk add sqlite mysql-client postgresql-client

FROM base AS prod

# This is required for prometheus_client to sync between uwsgi workers
RUN mkdir -p /tmp/prometheus_django_metrics;
RUN chown -R 1000:2000 /tmp/prometheus_django_metrics
ENV prometheus_multiproc_dir "/tmp/prometheus_django_metrics"

CMD [ "uwsgi", "--ini", "uwsgi.ini" ]
