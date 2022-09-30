# flake8: noqa

from .base import *

SECRET_KEY = "u5/IIbuiJR3Y9FQMBActk+btReZ5oOxu+l8MIJQWLfVzESoan5REE6UNSYYEQdjBOcty9CDak2X"

MIRAGE_SECRET_KEY = "V9u7DqZ6SrZHP+SvBT19dbB85NZJGgllpwYQ77BSr9kZ6n8ggXMfGd4sCll1TDcAPEolbVD8YbF"
MIRAGE_CIPHER_IV = "X+VFcDqtxJ5bbU+V"

BASE_URL = "http://localhost"

CELERY_BROKER_URL = "amqp://rabbitmq:rabbitmq@rabbit_test:5672"

DATABASES["default"] |= {
    "NAME": DATABASE_NAME or "oncall_local_dev",
    "USER": DATABASE_USER or "root",
    "PASSWORD": DATABASE_PASSWORD or "local_dev_pwd",
    "HOST": DATABASE_HOST or f"{DATABASE_TYPE}_test",
    "PORT": DATABASE_PORT or (3306 if DATABASE_TYPE == "mysql" else 5432),
}

# Dummy Telegram token (fake one)
TELEGRAM_TOKEN = "0000000000:XXXXXXXXXXXXXXXXXXXXXXXXXXXX-XXXXXX"

SENDGRID_FROM_EMAIL = "dummy_sendgrid_from_email@test.ci-test"
SENDGRID_SECRET_KEY = "dummy_sendgrid_secret_key"
TWILIO_ACCOUNT_SID = "dummy_twilio_account_sid"
TWILIO_AUTH_TOKEN = "dummy_twilio_auth_token"

EXTRA_MESSAGING_BACKENDS = [("apps.base.tests.messaging_backend.TestOnlyBackend", 42)]
