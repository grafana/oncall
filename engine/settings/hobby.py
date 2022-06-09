import sys
from random import randrange

# Workaround to use pymysql instead of mysqlclient
import pymysql

from .prod_without_db import *  # noqa

pymysql.install_as_MySQLdb()

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("MYSQL_DB_NAME"),
        "USER": os.environ.get("MYSQL_USER"),
        "PASSWORD": os.environ["MYSQL_PASSWORD"],
        "HOST": os.environ.get("MYSQL_HOST"),
        "PORT": os.environ.get("MYSQL_PORT"),
        "OPTIONS": {
            "charset": "utf8mb4",
            "connect_timeout": 1,
        },
    },
}

RABBITMQ_USERNAME = os.environ.get("RABBITMQ_USERNAME")
RABBITMQ_PASSWORD = os.environ.get("RABBITMQ_PASSWORD")
RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST")
RABBITMQ_PORT = os.environ.get("RABBITMQ_PORT")

CELERY_BROKER_URL = f"amqp://{RABBITMQ_USERNAME}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}"

MIRAGE_SECRET_KEY = SECRET_KEY
MIRAGE_CIPHER_IV = "1234567890abcdef"  # use default

APPEND_SLASH = False
SECURE_SSL_REDIRECT = False

# TODO: OSS: Add these setting to oss settings file. Add Version there too.
OSS_INSTALLATION_FEATURES_ENABLED = True

INSTALLED_APPS += ["apps.oss_installation"]  # noqa

CELERY_BEAT_SCHEDULE["send_usage_stats"] = {  # noqa
    "task": "apps.oss_installation.tasks.send_usage_stats_report",
    "schedule": crontab(hour=0, minute=randrange(0, 59)),  # Send stats report at a random minute past midnight  # noqa
    "args": (),
}  # noqa

CELERY_BEAT_SCHEDULE["send_cloud_heartbeat"] = {  # noqa
    "task": "apps.oss_installation.tasks.send_cloud_heartbeat",
    "schedule": crontab(minute="*/3"),  # noqa
    "args": (),
}  # noqa

SEND_ANONYMOUS_USAGE_STATS = True
