# flake8: noqa: F405
from .prod_without_db import *

DATABASE = os.getenv("DATABASE", default="mysql")
assert DATABASE in ["mysql", "sqlite"]

BROKER = os.getenv("BROKER", default="rabbitmq")
assert BROKER in ["rabbitmq", "redis"]

if DATABASE == "mysql":
    import pymysql

    pymysql.install_as_MySQLdb()

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ["MYSQL_DB_NAME"],
            "USER": os.environ["MYSQL_USER"],
            "PASSWORD": os.environ["MYSQL_PASSWORD"],
            "HOST": os.environ["MYSQL_HOST"],
            "PORT": os.environ["MYSQL_PORT"],
            "OPTIONS": {
                "charset": "utf8mb4",
                "connect_timeout": 1,
            },
        },
    }
elif DATABASE == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": "/var/lib/oncall/oncall.db",
        },
    }

if BROKER == "rabbitmq":
    RABBITMQ_USERNAME = os.environ["RABBITMQ_USERNAME"]
    RABBITMQ_PASSWORD = os.environ["RABBITMQ_PASSWORD"]
    RABBITMQ_HOST = os.environ["RABBITMQ_HOST"]
    RABBITMQ_PORT = os.environ["RABBITMQ_PORT"]
    CELERY_BROKER_URL = f"amqp://{RABBITMQ_USERNAME}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}"
elif BROKER == "redis":
    CELERY_BROKER_URL = os.environ["REDIS_URI"]

MIRAGE_SECRET_KEY = SECRET_KEY
MIRAGE_CIPHER_IV = "1234567890abcdef"  # use default

APPEND_SLASH = False
SECURE_SSL_REDIRECT = False
