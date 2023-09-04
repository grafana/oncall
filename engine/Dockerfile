FROM python:3.11.4-alpine3.18 AS base

# Create a group and user to run an app
ENV APP_USER=appuser
RUN addgroup --system --gid 2000 ${APP_USER} && \
    adduser --system --uid 1000 --ingroup ${APP_USER} ${APP_USER}

RUN apk add bash \
            python3-dev \
            build-base \
            linux-headers \
            pcre-dev \
            mariadb-connector-c-dev \
            libffi-dev \
            git \
            postgresql-dev 

WORKDIR /etc/app
COPY ./requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools wheel
RUN pip install -r requirements.txt

# we intentionally have two COPY commands, this is to have the requirements.txt in a separate build step
# which only invalidates when the requirements.txt actually changes. This avoids having to unneccasrily reinstall deps (which is time-consuming)
# https://stackoverflow.com/questions/34398632/docker-how-to-run-pip-requirements-txt-only-if-there-was-a-change/34399661#34399661
COPY ./ ./

# Collect static files
RUN DJANGO_SETTINGS_MODULE=settings.prod_without_db DATABASE_TYPE=sqlite3 DATABASE_NAME=/var/lib/oncall/oncall.db SECRET_KEY="ThEmUsTSecretKEYforBUILDstage123" SILK_PROFILER_ENABLED="True" python manage.py collectstatic --no-input

# Change permissions for the app folder, as previous commands run as root
RUN chown -R ${APP_USER}:${APP_USER} /etc/app

# Create SQLite database and set permissions
RUN mkdir -p /var/lib/oncall
RUN DATABASE_TYPE=sqlite3 DATABASE_NAME=/var/lib/oncall/oncall.db python manage.py create_sqlite_db
RUN chown -R ${APP_USER}:${APP_USER} /var/lib/oncall

# This is required for silk profilers to sync between uwsgi workers
RUN mkdir -p /tmp/silk_profiles;
RUN chown -R ${APP_USER}:${APP_USER} /tmp/silk_profiles

# This is required for prometheus_client to sync between uwsgi workers
RUN mkdir -p /tmp/prometheus_django_metrics;
RUN chown -R ${APP_USER}:${APP_USER} /tmp/prometheus_django_metrics
ENV prometheus_multiproc_dir "/tmp/prometheus_django_metrics"

CMD [ "uwsgi", "--ini", "uwsgi.ini" ]

FROM base AS dev
RUN apk add sqlite mysql-client postgresql-client
RUN pip install -r requirements-dev.txt

FROM dev AS dev-enterprise
RUN pip install -r requirements-enterprise-docker.txt

FROM base AS prod

# Change to a non-root user (number is required by Kubernetes runAsNonRoot check)
USER 1000

CMD [ "uwsgi", "--ini", "uwsgi.ini" ]
