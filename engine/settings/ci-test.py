# flake8: noqa

from .base import *

SECRET_KEY = "u5/IIbuiJR3Y9FQMBActk+btReZ5oOxu+l8MIJQWLfVzESoan5REE6UNSYYEQdjBOcty9CDak2X"

MIRAGE_SECRET_KEY = "V9u7DqZ6SrZHP+SvBT19dbB85NZJGgllpwYQ77BSr9kZ6n8ggXMfGd4sCll1TDcAPEolbVD8YbF"
MIRAGE_CIPHER_IV = "X+VFcDqtxJ5bbU+V"

BASE_URL = "http://localhost"

if DATABASE_TYPE == DatabaseTypes.SQLITE3:
    DATABASES["default"]["NAME"] = DATABASE_NAME or "oncall_ci.db"
else:
    DATABASES["default"] |= {
        "NAME": DATABASE_NAME or "oncall_local_dev",
        "USER": DATABASE_USER or DATABASE_DEFAULTS[DATABASE_TYPE]["USER"],
        "PASSWORD": DATABASE_PASSWORD or "local_dev_pwd",
        "HOST": DATABASE_HOST or f"{DATABASE_TYPE}_test",
        "PORT": DATABASE_PORT or DATABASE_DEFAULTS[DATABASE_TYPE]["PORT"],
    }

if BROKER_TYPE == BrokerTypes.RABBITMQ:
    CELERY_BROKER_URL = RABBITMQ_URI
elif BROKER_TYPE == BrokerTypes.REDIS:
    CELERY_BROKER_URL = REDIS_URI

# use redis as cache and celery broker on CI tests
if BROKER_TYPE != BrokerTypes.REDIS:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }

# Dummy Telegram token (fake one)
TELEGRAM_TOKEN = "0000000000:XXXXXXXXXXXXXXXXXXXXXXXXXXXX-XXXXXX"

TWILIO_ACCOUNT_SID = "dummy_twilio_account_sid"
TWILIO_AUTH_TOKEN = "dummy_twilio_auth_token"

EXTRA_MESSAGING_BACKENDS = [("apps.base.tests.messaging_backend.TestOnlyBackend", 42)]
