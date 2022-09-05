# flake8: noqa: F405

from .base import *  # noqa

SECRET_KEY = "u5/IIbuiJR3Y9FQMBActk+btReZ5oOxu+l8MIJQWLfVzESoan5REE6UNSYYEQdjBOcty9CDak2X"

MIRAGE_SECRET_KEY = "V9u7DqZ6SrZHP+SvBT19dbB85NZJGgllpwYQ77BSr9kZ6n8ggXMfGd4sCll1TDcAPEolbVD8YbF"
MIRAGE_CIPHER_IV = "X+VFcDqtxJ5bbU+V"

BASE_URL = "http://localhost"

CELERY_BROKER_URL = "amqp://rabbitmq:rabbitmq@rabbit_test:5672"

if DB_BACKEND == "mysql":
    # Workaround to use pymysql instead of mysqlclient
    import pymysql

    pymysql.install_as_MySQLdb()
    DB_BACKEND_DEFAULT_VALUES[DB_BACKEND]["OPTIONS"] = {"charset": "utf8mb4"}


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.{}".format(DB_BACKEND),
        "NAME": os.environ.get("DB_NAME", "oncall_local_dev"),
        "USER": os.environ.get("DB_USER", DB_BACKEND_DEFAULT_VALUES.get(DB_BACKEND, {}).get("USER", "root")),
        "PASSWORD": "local_dev_pwd",
        "HOST": "{}_test".format(DB_BACKEND),
        "PORT": os.environ.get("DB_PORT", DB_BACKEND_DEFAULT_VALUES.get(DB_BACKEND, {}).get("PORT", "3306")),
        "OPTIONS": DB_BACKEND_DEFAULT_VALUES.get(DB_BACKEND, {}).get("OPTIONS", {}),
    },
}

# Dummy Telegram token (fake one)
TELEGRAM_TOKEN = "0000000000:XXXXXXXXXXXXXXXXXXXXXXXXXXXX-XXXXXX"

SENDGRID_FROM_EMAIL = "dummy_sendgrid_from_email@test.ci-test"
SENDGRID_SECRET_KEY = "dummy_sendgrid_secret_key"
TWILIO_ACCOUNT_SID = "dummy_twilio_account_sid"
TWILIO_AUTH_TOKEN = "dummy_twilio_auth_token"

EXTRA_MESSAGING_BACKENDS = [("apps.base.tests.messaging_backend.TestOnlyBackend", 42)]
