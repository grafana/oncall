import os
import sys

from .base import *  # noqa

if DB_BACKEND == "mysql":  # noqa
    # Workaround to use pymysql instead of mysqlclient
    import pymysql

    pymysql.install_as_MySQLdb()

DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.{}".format(DB_BACKEND),  # noqa
        "NAME": os.environ.get("DB_NAME", "oncall_local_dev"),
        "USER": os.environ.get("DB_USER", DB_BACKEND_DEFAULT_VALUES.get(DB_BACKEND, {}).get("USER", "root")),  # noqa
        "PASSWORD": os.environ.get("DB_PASSWORD", "empty"),
        "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
        "PORT": os.environ.get("DB_PORT", DB_BACKEND_DEFAULT_VALUES.get(DB_BACKEND, {}).get("PORT", "3306")),  # noqa
        "OPTIONS": DB_BACKEND_DEFAULT_VALUES.get(DB_BACKEND, {}).get("OPTIONS", {}),  # noqa
    },
}

CACHES["default"]["LOCATION"] = ["localhost:6379"]  # noqa: F405

SECRET_KEY = os.environ.get("SECRET_KEY", "osMsNM0PqlRHBlUvqmeJ7+ldU3IUETCrY9TrmiViaSmInBHolr1WUlS0OFS4AHrnnkp1vp9S9z1")

MIRAGE_SECRET_KEY = os.environ.get(
    "MIRAGE_SECRET_KEY", "sIrmyTvh+Go+h/2E46SnYGwgkKyH6IF6MXZb65I40HVCbj0+dD3JvpAqppEwFb7Vxnxlvtey+EL"
)
MIRAGE_CIPHER_IV = os.environ.get("MIRAGE_CIPHER_IV", "tZZa+60zTZO2NRcS")

TESTING = "pytest" in sys.modules or "unittest" in sys.modules

CELERY_BROKER_URL = "pyamqp://rabbitmq:rabbitmq@localhost:5672"

SILKY_PYTHON_PROFILER = True

# For any requests that come in with that header/value, request.is_secure() will return True.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Uncomment this to view SQL queries
# LOGGING = {
#     'version': 1,
#     'filters': {
#         'require_debug_true': {
#             '()': 'django.utils.log.RequireDebugTrue',
#         }
#     },
#     'handlers': {
#         'console': {
#             'level': 'DEBUG',
#             'filters': ['require_debug_true'],
#             'class': 'logging.StreamHandler',
#         }
#     },
#     'loggers': {
#         'django.db.backends': {
#             'level': 'DEBUG',
#             'handlers': ['console'],
#         }
#     }
# }

SILKY_INTERCEPT_PERCENT = 100

SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Basic": {"type": "basic"},
        "Bearer": {"type": "apiKey", "name": "Authorization", "in": "header"},
    },
    "SUPPORTED_SUBMIT_METHODS": ["get", "post", "put", "delete", "options"],
}

if TESTING:
    EXTRA_MESSAGING_BACKENDS = [("apps.base.tests.messaging_backend.TestOnlyBackend", 42)]
    TELEGRAM_TOKEN = "0000000000:XXXXXXXXXXXXXXXXXXXXXXXXXXXX-XXXXXX"
    TWILIO_AUTH_TOKEN = "twilio_auth_token"
