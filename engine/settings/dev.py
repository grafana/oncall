import os
import sys

from .base import *  # noqa

SECRET_KEY = os.environ.get("SECRET_KEY", "osMsNM0PqlRHBlUvqmeJ7+ldU3IUETCrY9TrmiViaSmInBHolr1WUlS0OFS4AHrnnkp1vp9S9z1")

MIRAGE_SECRET_KEY = os.environ.get(
    "MIRAGE_SECRET_KEY", "sIrmyTvh+Go+h/2E46SnYGwgkKyH6IF6MXZb65I40HVCbj0+dD3JvpAqppEwFb7Vxnxlvtey+EL"
)
MIRAGE_CIPHER_IV = os.environ.get("MIRAGE_CIPHER_IV", "tZZa+60zTZO2NRcS")

# Primary database must have the name "default"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "sqlite_data/db.sqlite3"),  # noqa
    },
}

TESTING = "pytest" in sys.modules or "unittest" in sys.modules

READONLY_DATABASES = {}

# Dictionaries concatenation, introduced in python3.9
DATABASES = DATABASES | READONLY_DATABASES

CACHES = {
    "default": {
        "BACKEND": "redis_cache.RedisCache",
        "LOCATION": [
            "localhost:6379",
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
    FEATURE_EXTRA_MESSAGING_BACKENDS_ENABLED = True
    EXTRA_MESSAGING_BACKENDS = ["apps.base.tests.messaging_backend.TestOnlyBackend"]
    TELEGRAM_TOKEN = "0000000000:XXXXXXXXXXXXXXXXXXXXXXXXXXXX-XXXXXX"
    TWILIO_AUTH_TOKEN = "twilio_auth_token"
