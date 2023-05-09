FROM python:3.11.3-slim-buster AS base
RUN apt-get update && apt-get install -y \
    python3-dev \
    gcc \
    libmariadb-dev \
    libpq-dev \
    netcat \
    curl \
    bash \
    git

WORKDIR /etc/app
COPY ./requirements.txt ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# we intentionally have two COPY commands, this is to have the requirements.txt in a separate build step
# which only invalidates when the requirements.txt actually changes. This avoids having to unneccasrily reinstall deps (which is time-consuming)
# https://stackoverflow.com/questions/34398632/docker-how-to-run-pip-requirements-txt-only-if-there-was-a-change/34399661#34399661
COPY ./ ./

# Collect static files and create an SQLite database
RUN mkdir -p /var/lib/oncall
RUN DJANGO_SETTINGS_MODULE=settings.prod_without_db DATABASE_TYPE=sqlite3 DATABASE_NAME=/var/lib/oncall/oncall.db SECRET_KEY="ThEmUsTSecretKEYforBUILDstage123" SILK_PROFILER_ENABLED="True" python manage.py collectstatic --no-input
RUN chown -R 1000:2000 /var/lib/oncall

# This is required for silk profilers to sync between uwsgi workers
RUN mkdir -p /tmp/silk_profiles;
RUN chown -R 1000:2000 /tmp/silk_profiles

FROM base AS dev
RUN apt-get install -y sqlite3 default-mysql-client postgresql-client

FROM dev AS dev-enterprise
RUN pip install -r requirements-enterprise-docker.txt

FROM base AS prod

# This is required for prometheus_client to sync between uwsgi workers
RUN mkdir -p /tmp/prometheus_django_metrics;
RUN chown -R 1000:2000 /tmp/prometheus_django_metrics
ENV prometheus_multiproc_dir "/tmp/prometheus_django_metrics"

CMD [ "uwsgi", "--ini", "uwsgi.ini" ]
