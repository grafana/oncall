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

# always use in-memory cache for testing.. this makes things alot easier wrt pytest-xdist (parallel test execution)
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

# if you have django-silk enabled when running the tests it can lead to some weird errors like:
# RuntimeError: Database access not allowed, use the "django_db" mark, or the "db" or "transactional_db"
# fixtures to enable it.
#
# ERROR    django.request:log.py:241 Internal Server Error: /startupprobe/
# Traceback (most recent call last):
#   File "/usr/local/lib/python3.12/site-packages/django/core/handlers/exception.py", line 55, in inner
#     response = get_response(request)
#                ^^^^^^^^^^^^^^^^^^^^^
#   File "/usr/local/lib/python3.12/site-packages/silk/middleware.py", line 70, in __call__
#     self.process_request(request)
#   File "/usr/local/lib/python3.12/site-packages/silk/middleware.py", line 120, in process_request
#     request_model = RequestModelFactory(request).construct_request_model()
#                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "/usr/local/lib/python3.12/site-packages/silk/model_factory.py", line 243, in construct_request_model
#     request_model = models.Request.objects.create(
SILK_PROFILER_ENABLED = False
