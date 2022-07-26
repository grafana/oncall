# flake8: noqa: F405

# Workaround to use pymysql instead of mysqlclient
import pymysql

from .ci_test_without_db import *  # noqa

pymysql.install_as_MySQLdb()

# Primary database must have the name "default"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "oncall_local_dev",
        "USER": "root",
        "PASSWORD": "local_dev_pwd",
        "HOST": "mysql_test",
        "PORT": "3306",
        "OPTIONS": {"charset": "utf8mb4"},
    },
}
