# flake8: noqa
import os
import socket
import sys

from .base import *

# DEBUG is disabled by default because it can cause slowness when making several consecutive requests
DEBUG = getenv_boolean("DEBUG", default=False)

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

SECRET_KEY = os.environ.get("SECRET_KEY", "osMsNM0PqlRHBlUvqmeJ7+ldU3IUETCrY9TrmiViaSmInBHolr1WUlS0OFS4AHrnnkp1vp9S9z1")
MIRAGE_SECRET_KEY = os.environ.get(
    "MIRAGE_SECRET_KEY", "sIrmyTvh+Go+h/2E46SnYGwgkKyH6IF6MXZb65I40HVCbj0+dD3JvpAqppEwFb7Vxnxlvtey+EL"
)
MIRAGE_CIPHER_IV = os.environ.get("MIRAGE_CIPHER_IV", "tZZa+60zTZO2NRcS")

TESTING = "pytest" in sys.modules or "unittest" in sys.modules

# For any requests that come in with that header/value, request.is_secure() will return True.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if getenv_boolean("DEV_DEBUG_VIEW_SQL_QUERIES", default=False):
    LOGGING = {
        "version": 1,
        "filters": {
            "require_debug_true": {
                "()": "django.utils.log.RequireDebugTrue",
            }
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "filters": ["require_debug_true"],
                "class": "logging.StreamHandler",
            }
        },
        "loggers": {
            "django.db.backends": {
                "level": "DEBUG",
                "handlers": ["console"],
            }
        },
    }

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

INTERNAL_IPS = [
    "127.0.0.1",
]

try:
    # # the below two lines make it possible to use django-debug-toolbar inside of docker locally
    # # https://knasmueller.net/fix-djangos-debug-toolbar-not-showing-inside-docker
    # # https://stackoverflow.com/questions/10517765/django-debug-toolbar-not-showing-up
    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS += [".".join(ip.split(".")[:-1] + ["1"]) for ip in ips]
except OSError:
    # usually raised if this is being run outside of a docker container context
    INTERNAL_IPS = []
