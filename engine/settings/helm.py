import os

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
RABBITMQ_PROTOCOL = os.environ.get("RABBITMQ_PROTOCOL")
RABBITMQ_VHOST = os.environ.get("RABBITMQ_VHOST", "")

CELERY_BROKER_URL = (
    f"{RABBITMQ_PROTOCOL}://{RABBITMQ_USERNAME}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/{RABBITMQ_VHOST}"
)

APPEND_SLASH = False
SECURE_SSL_REDIRECT = False
