# flake8: noqa
import os
import sys

from .base import *

DEBUG = True

if DATABASE_TYPE == DatabaseTypes.SQLITE3:
    DATABASES["default"]["NAME"] = DATABASE_NAME or "oncall_dev.db"
else:
    DATABASES["default"] |= {
        "NAME": DATABASE_NAME or "oncall_local_dev",
        "USER": DATABASE_USER or DATABASE_DEFAULTS[DATABASE_TYPE]["USER"],
        "PASSWORD": DATABASE_PASSWORD or "empty",
        "HOST": DATABASE_HOST or "127.0.0.1",
        "PORT": DATABASE_PORT or DATABASE_DEFAULTS[DATABASE_TYPE]["PORT"],
    }

if BROKER_TYPE == BrokerTypes.RABBITMQ:
    CELERY_BROKER_URL = "pyamqp://rabbitmq:rabbitmq@localhost:5672"
elif BROKER_TYPE == BrokerTypes.REDIS:
    CELERY_BROKER_URL = "redis://localhost:6379"

CACHES["default"]["LOCATION"] = ["localhost:6379"]

SECRET_KEY = os.environ.get("SECRET_KEY", "osMsNM0PqlRHBlUvqmeJ7+ldU3IUETCrY9TrmiViaSmInBHolr1WUlS0OFS4AHrnnkp1vp9S9z1")

MIRAGE_SECRET_KEY = os.environ.get(
    "MIRAGE_SECRET_KEY", "sIrmyTvh+Go+h/2E46SnYGwgkKyH6IF6MXZb65I40HVCbj0+dD3JvpAqppEwFb7Vxnxlvtey+EL"
)
MIRAGE_CIPHER_IV = os.environ.get("MIRAGE_CIPHER_IV", "tZZa+60zTZO2NRcS")

TESTING = "pytest" in sys.modules or "unittest" in sys.modules

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
