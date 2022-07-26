# flake8: noqa: F405

from .ci_test_without_db import *  # noqa

# Primary database must have the name "default"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "oncall_local_dev",
        "USER": "postgres",
        "PASSWORD": "local_dev_pwd",
        "HOST": "postgresql_test",
        "PORT": "5432",
    },
}
