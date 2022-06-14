import os
import sys

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

REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")
REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PORT = os.environ.get("REDIS_PORT", "6379")
REDIS_URI = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}"

CACHES = {
    "default": {
        "BACKEND": "redis_cache.RedisCache",
        "LOCATION": [
            REDIS_URI,
        ],
        "OPTIONS": {
            "DB": 1,
            "PARSER_CLASS": "redis.connection.HiredisParser",
            "CONNECTION_POOL_CLASS": "redis.BlockingConnectionPool",
            "CONNECTION_POOL_CLASS_KWARGS": {
                "max_connections": 50,
                "timeout": 20,
            },
            "MAX_CONNECTIONS": 1000,
            "PICKLE_VERSION": -1,
        },
    },
}

APPEND_SLASH = False
SECURE_SSL_REDIRECT = False

TESTING = "pytest" in sys.modules or "unittest" in sys.modules


if TESTING:
    TELEGRAM_TOKEN = "0000000000:XXXXXXXXXXXXXXXXXXXXXXXXXXXX-XXXXXX"
    TWILIO_AUTH_TOKEN = "twilio_auth_token"

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
