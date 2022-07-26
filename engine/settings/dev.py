import os

# Workaround to use pymysql instead of mysqlclient
import pymysql

from .dev_without_db import *  # noqa

pymysql.install_as_MySQLdb()

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("MYSQL_DB_NAME", "oncall_local_dev"),
        "USER": os.environ.get("MYSQL_USER", "root"),
        "PASSWORD": os.environ.get("MYSQL_PASSWORD"),
        "HOST": os.environ.get("MYSQL_HOST", "127.0.0.1"),
        "PORT": os.environ.get("MYSQL_PORT", "3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
            "connect_timeout": 1,
        },
    },
}

READONLY_DATABASES = {}

# Dictionaries concatenation, introduced in python3.9
DATABASES = DATABASES | READONLY_DATABASES
