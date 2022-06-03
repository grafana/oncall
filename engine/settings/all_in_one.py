import sys
from random import randrange

from .prod_without_db import *  # noqa

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "sqlite_data/db.sqlite3"),  # noqa
    },
}

TESTING = "pytest" in sys.modules or "unittest" in sys.modules

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

CELERY_BROKER_URL = "redis://localhost:6379/0"

if TESTING:
    TELEGRAM_TOKEN = "0000000000:XXXXXXXXXXXXXXXXXXXXXXXXXXXX-XXXXXX"
    TWILIO_AUTH_TOKEN = "twilio_auth_token"

# TODO: OSS: Add these setting to oss settings file. Add Version there too.
OSS_INSTALLATION_FEATURES_ENABLED = True

INSTALLED_APPS += ["apps.oss_installation"]  # noqa

CELERY_BEAT_SCHEDULE["send_usage_stats"] = {  # noqa
    "task": "apps.oss_installation.tasks.send_usage_stats_report",
    "schedule": crontab(hour=0, minute=randrange(0, 59)),  # Send stats report at a random minute past midnight  # noqa
    "args": (),
}  # noqa

CELERY_BEAT_SCHEDULE["send_cloud_heartbeat"] = {  # noqa
    "task": "apps.oss_installation.tasks.send_cloud_heartbeat",
    "schedule": crontab(minute="*/3"),  # noqa
    "args": (),
}  # noqa

SEND_ANONYMOUS_USAGE_STATS = True
