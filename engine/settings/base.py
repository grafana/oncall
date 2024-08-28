import base64
import json
import os
import typing
from random import randrange

from celery.schedules import crontab
from firebase_admin import credentials, initialize_app

from common.utils import getenv_boolean, getenv_integer, getenv_list

VERSION = "dev-oss"
SEND_ANONYMOUS_USAGE_STATS = getenv_boolean("SEND_ANONYMOUS_USAGE_STATS", default=True)

# License is OpenSource or Cloud
OPEN_SOURCE_LICENSE_NAME = "OpenSource"
CLOUD_LICENSE_NAME = "Cloud"
LICENSE = os.environ.get("ONCALL_LICENSE", default=OPEN_SOURCE_LICENSE_NAME)
IS_OPEN_SOURCE = LICENSE == OPEN_SOURCE_LICENSE_NAME
CURRENTLY_UNDERGOING_MAINTENANCE_MESSAGE = os.environ.get("CURRENTLY_UNDERGOING_MAINTENANCE_MESSAGE", None)
IS_IN_MAINTENANCE_MODE = CURRENTLY_UNDERGOING_MAINTENANCE_MESSAGE is not None

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY")
TOKEN_SECRET = os.environ.get("TOKEN_SECRET", SECRET_KEY)
# TO generate it use
# cat /dev/urandom | base64 | tr -dc '0-9a-zA-Z!@#$%^&*(-_=+)' | head -c75
TOKEN_SALT = os.environ.get("TOKEN_SALT", "")

# django-mirage-field related settings
MIRAGE_SECRET_KEY = os.environ.get("MIRAGE_SECRET_KEY")
MIRAGE_CIPHER_IV = os.environ.get("MIRAGE_CIPHER_IV")
MIRAGE_CIPHER_MODE = "CBC"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

DEBUG_CELERY_TASKS_PROFILING = getenv_boolean("DEBUG_CELERY_TASKS_PROFILING", False)

OTEL_TRACING_ENABLED = getenv_boolean("OTEL_TRACING_ENABLED", False)
OTEL_EXPORTER_OTLP_ENDPOINT = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")

ALLOWED_HOSTS = [item.strip() for item in os.environ.get("ALLOWED_HOSTS", "*").split(",")]

DOCS_URL = "https://grafana.com/docs/oncall/latest/"

# Settings of running OnCall instance.
BASE_URL = os.environ.get("BASE_URL")  # Root URL of OnCall backend

# Feature toggles
FEATURE_LIVE_SETTINGS_ENABLED = getenv_boolean("FEATURE_LIVE_SETTINGS_ENABLED", default=True)
FEATURE_TELEGRAM_INTEGRATION_ENABLED = getenv_boolean("FEATURE_TELEGRAM_INTEGRATION_ENABLED", default=True)
FEATURE_TELEGRAM_LONG_POLLING_ENABLED = getenv_boolean("FEATURE_TELEGRAM_LONG_POLLING_ENABLED", default=False)
FEATURE_EMAIL_INTEGRATION_ENABLED = getenv_boolean("FEATURE_EMAIL_INTEGRATION_ENABLED", default=True)
FEATURE_SLACK_INTEGRATION_ENABLED = getenv_boolean("FEATURE_SLACK_INTEGRATION_ENABLED", default=True)
FEATURE_MULTIREGION_ENABLED = getenv_boolean("FEATURE_MULTIREGION_ENABLED", default=False)
FEATURE_INBOUND_EMAIL_ENABLED = getenv_boolean("FEATURE_INBOUND_EMAIL_ENABLED", default=True)
FEATURE_PROMETHEUS_EXPORTER_ENABLED = getenv_boolean("FEATURE_PROMETHEUS_EXPORTER_ENABLED", default=False)
FEATURE_GRAFANA_ALERTING_V2_ENABLED = getenv_boolean("FEATURE_GRAFANA_ALERTING_V2_ENABLED", default=True)
GRAFANA_CLOUD_ONCALL_HEARTBEAT_ENABLED = getenv_boolean("GRAFANA_CLOUD_ONCALL_HEARTBEAT_ENABLED", default=True)
GRAFANA_CLOUD_NOTIFICATIONS_ENABLED = getenv_boolean("GRAFANA_CLOUD_NOTIFICATIONS_ENABLED", default=True)
# Enable labels feature fo all organizations. This flag overrides FEATURE_LABELS_ENABLED_FOR_GRAFANA_ORGS
FEATURE_LABELS_ENABLED_FOR_ALL = getenv_boolean("FEATURE_LABELS_ENABLED_FOR_ALL", default=False)
# Enable labels feature for organizations from the list. Use OnCall organization ID, for this flag
FEATURE_LABELS_ENABLED_PER_ORG = getenv_list("FEATURE_LABELS_ENABLED_PER_ORG", default=list())
FEATURE_ALERT_GROUP_SEARCH_ENABLED = getenv_boolean("FEATURE_ALERT_GROUP_SEARCH_ENABLED", default=True)
FEATURE_ALERT_GROUP_SEARCH_CUTOFF_DAYS = getenv_integer("FEATURE_ALERT_GROUP_SEARCH_CUTOFF_DAYS", default=None)
FEATURE_NOTIFICATION_BUNDLE_ENABLED = getenv_boolean("FEATURE_NOTIFICATION_BUNDLE_ENABLED", default=True)

TWILIO_API_KEY_SID = os.environ.get("TWILIO_API_KEY_SID")
TWILIO_API_KEY_SECRET = os.environ.get("TWILIO_API_KEY_SECRET")
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.environ.get("TWILIO_NUMBER")
TWILIO_VERIFY_SERVICE_SID = os.environ.get("TWILIO_VERIFY_SERVICE_SID")
PHONE_NOTIFICATIONS_LIMIT = getenv_integer("PHONE_NOTIFICATIONS_LIMIT", 200)

TELEGRAM_WEBHOOK_HOST = os.environ.get("TELEGRAM_WEBHOOK_HOST", BASE_URL)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# For Grafana Cloud integration
GRAFANA_CLOUD_ONCALL_API_URL = os.environ.get(
    "GRAFANA_CLOUD_ONCALL_API_URL", "https://oncall-prod-us-central-0.grafana.net/oncall"
)
GRAFANA_CLOUD_ONCALL_TOKEN = os.environ.get("GRAFANA_CLOUD_ONCALL_TOKEN", None)

# Outgoing webhook settings
DANGEROUS_WEBHOOKS_ENABLED = getenv_boolean("DANGEROUS_WEBHOOKS_ENABLED", default=False)
OUTGOING_WEBHOOK_TIMEOUT = getenv_integer("OUTGOING_WEBHOOK_TIMEOUT", default=4)
WEBHOOK_RESPONSE_LIMIT = 50000

# Multiregion settings
ONCALL_GATEWAY_URL = os.environ.get("ONCALL_GATEWAY_URL", "")
ONCALL_GATEWAY_API_TOKEN = os.environ.get("ONCALL_GATEWAY_API_TOKEN", "")
ONCALL_BACKEND_REGION = os.environ.get("ONCALL_BACKEND_REGION")
UNIFIED_SLACK_APP_ENABLED = getenv_boolean("UNIFIED_SLACK_APP_ENABLED", default=False)
# secret to verify the incoming requests from the chatops-proxy
CHATOPS_SIGNING_SECRET = os.environ.get("CHATOPS_SIGNING_SECRET", None)

# Prometheus exporter metrics endpoint auth
PROMETHEUS_EXPORTER_SECRET = os.environ.get("PROMETHEUS_EXPORTER_SECRET")
# Application metric names without prefixes
METRIC_ALERT_GROUPS_TOTAL_NAME = "alert_groups_total"
METRIC_ALERT_GROUPS_RESPONSE_TIME_NAME = "alert_groups_response_time"
METRIC_USER_WAS_NOTIFIED_OF_ALERT_GROUPS_NAME = "user_was_notified_of_alert_groups"
METRICS_ALL = [
    METRIC_ALERT_GROUPS_TOTAL_NAME,
    METRIC_ALERT_GROUPS_RESPONSE_TIME_NAME,
    METRIC_USER_WAS_NOTIFIED_OF_ALERT_GROUPS_NAME,
]
# List of metrics to collect. Collect all available application metrics by default
METRICS_TO_COLLECT = getenv_list("METRICS_TO_COLLECT", METRICS_ALL)


# Database
class DatabaseTypes:
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    SQLITE3 = "sqlite3"


DATABASE_DEFAULTS = {
    DatabaseTypes.MYSQL: {
        "USER": "root",
        "PORT": 3306,
    },
    DatabaseTypes.POSTGRESQL: {
        "USER": "postgres",
        "PORT": 5432,
    },
}

DATABASE_TYPES = DatabaseTypes
DATABASE_NAME = os.getenv("DATABASE_NAME") or os.getenv("MYSQL_DB_NAME")
DATABASE_USER = os.getenv("DATABASE_USER") or os.getenv("MYSQL_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD") or os.getenv("MYSQL_PASSWORD")
DATABASE_HOST = os.getenv("DATABASE_HOST") or os.getenv("MYSQL_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT") or os.getenv("MYSQL_PORT")

DATABASE_OPTIONS = os.getenv("DATABASE_OPTIONS")
if DATABASE_OPTIONS:
    try:
        DATABASE_OPTIONS = dict([tuple(i.split("=")) for i in str(DATABASE_OPTIONS).split(" ")])
    except Exception:
        raise Exception("Bad database options. Check DATABASE_OPTIONS variable")
else:
    DATABASE_OPTIONS = {}

DATABASE_TYPE = os.getenv("DATABASE_TYPE", DatabaseTypes.MYSQL).lower()
assert DATABASE_TYPE in {DatabaseTypes.MYSQL, DatabaseTypes.POSTGRESQL, DatabaseTypes.SQLITE3}

DATABASE_ENGINE = f"django.db.backends.{DATABASE_TYPE}"

DatabaseConfig = typing.Dict[str, typing.Dict[str, typing.Any]]

DATABASE_CONFIGS: DatabaseConfig = {
    DatabaseTypes.SQLITE3: {
        "ENGINE": DATABASE_ENGINE,
        "NAME": DATABASE_NAME or "/var/lib/oncall/oncall.db",
    },
    DatabaseTypes.MYSQL: {
        "ENGINE": DATABASE_ENGINE,
        "NAME": DATABASE_NAME,
        "USER": DATABASE_USER,
        "PASSWORD": DATABASE_PASSWORD,
        "HOST": DATABASE_HOST,
        "PORT": DATABASE_PORT,
        "OPTIONS": DATABASE_OPTIONS
        | {
            "charset": "utf8mb4",
            "connect_timeout": 1,
        },
    },
    DatabaseTypes.POSTGRESQL: {
        "ENGINE": DATABASE_ENGINE,
        "NAME": DATABASE_NAME,
        "USER": DATABASE_USER,
        "PASSWORD": DATABASE_PASSWORD,
        "HOST": DATABASE_HOST,
        "PORT": DATABASE_PORT,
        "OPTIONS": DATABASE_OPTIONS,
    },
}

READONLY_DATABASES: DatabaseConfig = {}
DATABASES = {
    "default": DATABASE_CONFIGS[DATABASE_TYPE],
}
if DATABASE_TYPE == DatabaseTypes.MYSQL:
    # Workaround to use pymysql instead of mysqlclient
    import pymysql

    pymysql.install_as_MySQLdb()

DJANGO_MYSQL_REWRITE_QUERIES = True

ALERT_GROUPS_DISABLE_PREFER_ORDERING_INDEX = DATABASE_TYPE == DatabaseTypes.MYSQL and getenv_boolean(
    "ALERT_GROUPS_DISABLE_PREFER_ORDERING_INDEX", default=False
)
ALERT_GROUP_LIST_TRY_PREFETCH = getenv_boolean("ALERT_GROUP_LIST_TRY_PREFETCH", default=False)

# Redis
REDIS_USERNAME = os.getenv("REDIS_USERNAME", "")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)
REDIS_DATABASE = os.getenv("REDIS_DATABASE", 1)
REDIS_PROTOCOL = os.getenv("REDIS_PROTOCOL", "redis")

REDIS_URI = os.getenv("REDIS_URI")
if not REDIS_URI:
    REDIS_URI = f"{REDIS_PROTOCOL}://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DATABASE}"

USE_REDIS_CLUSTER = getenv_boolean("USE_REDIS_CLUSTER", default=False)
REDIS_USE_SSL = os.getenv("REDIS_USE_SSL")
REDIS_SSL_CONFIG = {}

if REDIS_USE_SSL:
    import ssl

    REDIS_SSL_CA_CERTS = os.getenv("REDIS_SSL_CA_CERTS")
    if REDIS_SSL_CA_CERTS:
        REDIS_SSL_CONFIG["ssl_ca_certs"] = REDIS_SSL_CA_CERTS

    REDIS_SSL_CERTFILE = os.getenv("REDIS_SSL_CERTFILE")
    if REDIS_SSL_CERTFILE:
        REDIS_SSL_CONFIG["ssl_certfile"] = REDIS_SSL_CERTFILE

    REDIS_SSL_KEYFILE = os.getenv("REDIS_SSL_KEYFILE")
    if REDIS_SSL_KEYFILE:
        REDIS_SSL_CONFIG["ssl_keyfile"] = REDIS_SSL_KEYFILE

    REDIS_SSL_CERT_REQS = os.getenv("REDIS_SSL_CERT_REQS")  # CERT_NONE, CERT_OPTIONAL, or CERT_REQUIRED
    if REDIS_SSL_CERT_REQS:
        REDIS_SSL_CONFIG["ssl_cert_reqs"] = getattr(ssl, str(REDIS_SSL_CERT_REQS).upper())

# Cache
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URI,
        "OPTIONS": {
            "DB": REDIS_DATABASE,
            "PARSER_CLASS": "redis.connection._HiredisParser",
            "CONNECTION_POOL_CLASS": "redis.BlockingConnectionPool",
            "CONNECTION_POOL_CLASS_KWARGS": REDIS_SSL_CONFIG
            | {
                "max_connections": 50,
                "timeout": 20,
            },
            "MAX_CONNECTIONS": 1000,
            "PICKLE_VERSION": -1,
        },
    },
}

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "mirage",
    "engine",
    "apps.user_management",
    "apps.alerts",
    "apps.integrations",
    "apps.schedules",
    "apps.heartbeat",
    "apps.email",
    "apps.slack",
    "apps.telegram",
    "apps.twilioapp",
    "apps.mobile_app",
    "apps.api",
    "apps.api_for_grafana_incident",
    "apps.base",
    "apps.auth_token",
    "apps.public_api",
    "apps.grafana_plugin",
    "apps.webhooks",
    "apps.metrics_exporter",
    "apps.labels",
    "corsheaders",
    "debug_toolbar",
    "social_django",
    "polymorphic",
    "django_migration_linter",
    "fcm_django",
    "django_dbconn_retry",
    "apps.phone_notifications",
    "drf_spectacular",
    "apps.google",
    "apps.chatops_proxy",
]

if DATABASE_TYPE == DatabaseTypes.MYSQL:
    INSTALLED_APPS += ["django_mysql"]

REST_FRAMEWORK = {
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_SCHEMA_CLASS": "engine.schema.CustomAutoSchema",
}


DRF_SPECTACULAR_ENABLED = getenv_boolean("DRF_SPECTACULAR_ENABLED", default=False)

SPECTACULAR_SETTINGS = {
    "TITLE": "Grafana OnCall Private API",
    "DESCRIPTION": "Internal API docs. This is not meant to be used by end users. API endpoints will be kept added/removed/changed without notice.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # OTHER SETTINGS
    "PREPROCESSING_HOOKS": [
        "engine.included_path.custom_preprocessing_hook"  # Custom hook to include only paths from SPECTACULAR_INCLUDED_PATHS
    ],
    "SERVE_URLCONF": ("apps.api.urls"),
    "SWAGGER_UI_SETTINGS": {
        "supportedSubmitMethods": [],  # Disable "Try it out" button for all endpoints
    },
}
# Use custom scheme if env var exists
SWAGGER_UI_SETTINGS_URL = os.getenv("SWAGGER_UI_SETTINGS_URL")
if SWAGGER_UI_SETTINGS_URL:
    SPECTACULAR_SETTINGS["SWAGGER_UI_SETTINGS"]["url"] = SWAGGER_UI_SETTINGS_URL

SPECTACULAR_INCLUDED_PATHS = [
    "/features",
    "/alertgroups",
    "/alert_receive_channels",
    # current user endpoint 👇, without trailing slash we pick-up /user_group endpoints, which we don't want for now
    "/user/",
    "/users",
    "/labels",
    # social auth routes
    "/login",
    "/complete",
    "/disconnect",
]

MIDDLEWARE = [
    "log_request_id.middleware.RequestIDMiddleware",
    "engine.middlewares.RequestTimeLoggingMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "social_django.middleware.SocialAuthExceptionMiddleware",
    "apps.social_auth.middlewares.SocialAuthAuthCanceledExceptionMiddleware",
    "apps.integrations.middlewares.IntegrationExceptionMiddleware",
    "apps.user_management.middlewares.OrganizationMovedMiddleware",
    "apps.user_management.middlewares.OrganizationDeletedMiddleware",
]

if OTEL_TRACING_ENABLED:
    MIDDLEWARE.insert(0, "engine.middlewares.LogRequestHeadersMiddleware")

LOG_REQUEST_ID_HEADER = "HTTP_X_CLOUD_TRACE_CONTEXT"
LOG_CELERY_TASK_ARGUMENTS = getenv_boolean("LOG_CELERY_TASK_ARGUMENTS", default=True)

log_fmt = "source=engine:app google_trace_id=%(request_id)s logger=%(name)s %(message)s"

if OTEL_TRACING_ENABLED:
    log_fmt = (
        "source=engine:app trace_id=%(otelTraceID)s span_id=%("
        "otelSpanID)s trace_sampled=%(otelTraceSampled)s google_trace_id=%(request_id)s logger=%(name)s %(message)s"
    )
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"request_id": {"()": "log_request_id.filters.RequestIDFilter"}},
    "formatters": {
        "standard": {"format": log_fmt},
        "insight_logger": {"format": "insight=true logger=%(name)s %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["request_id"],
            "formatter": "standard",
        },
        "insight_logger": {
            "class": "logging.StreamHandler",
            "formatter": "insight_logger",
        },
    },
    "loggers": {
        "insight_logger": {
            "handlers": ["insight_logger"],
            "level": "INFO",
            "propagate": False,
        },
        "": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
    },
}

ROOT_URLCONF = os.environ.get("ROOT_URLCONF", "engine.urls")

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "engine.wsgi.application"

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = os.environ.get("STATIC_URL", "/static/")
STATIC_ROOT = "./static/"

# RabbitMQ
RABBITMQ_USERNAME = os.getenv("RABBITMQ_USERNAME")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT", 5672)
RABBITMQ_PROTOCOL = os.getenv("RABBITMQ_PROTOCOL", "amqp")
RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST", "")

RABBITMQ_URI = os.getenv("RABBITMQ_URI") or os.getenv("RABBIT_URI")
if not RABBITMQ_URI:
    RABBITMQ_URI = f"{RABBITMQ_PROTOCOL}://{RABBITMQ_USERNAME}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/{RABBITMQ_VHOST}"


# Celery
class BrokerTypes:
    RABBITMQ = "rabbitmq"
    REDIS = "redis"


BROKER_TYPE = os.getenv("BROKER_TYPE", BrokerTypes.RABBITMQ).lower()
assert BROKER_TYPE in {BrokerTypes.RABBITMQ, BrokerTypes.REDIS}

if BROKER_TYPE == BrokerTypes.RABBITMQ:
    CELERY_BROKER_URL = RABBITMQ_URI
elif BROKER_TYPE == BrokerTypes.REDIS:
    CELERY_BROKER_URL = REDIS_URI
    if REDIS_USE_SSL:
        CELERY_BROKER_USE_SSL = REDIS_SSL_CONFIG
else:
    raise ValueError(f"Invalid BROKER_TYPE env variable: {BROKER_TYPE}")

# By default, apply_async will just hang indefinitely trying to reach to RabbitMQ even if RabbitMQ is down.
# This makes apply_async retry 3 times trying to reach to RabbitMQ, with some extra info on periods between retries.
# https://docs.celeryproject.org/en/stable/userguide/configuration.html#std-setting-broker_transport_options
# Note that max_retries is not related to task retries, but to rabbitmq specific kombu settings.
CELERY_BROKER_TRANSPORT_OPTIONS = {"max_retries": 3, "interval_start": 0, "interval_step": 0.2, "interval_max": 0.5}

CELERY_IGNORE_RESULT = True
CELERY_ACKS_LATE = True

CELERY_TASK_ACKS_LATE = True

CELERY_WORKER_CONCURRENCY = 1
CELERY_MAX_TASKS_PER_CHILD = 1

CELERY_WORKER_SEND_TASK_EVENTS = True
CELERY_TASK_SEND_SENT_EVENT = True

ESCALATION_AUDITOR_ENABLED = getenv_boolean("ESCALATION_AUDITOR_ENABLED", default=True)
ALERT_GROUP_ESCALATION_AUDITOR_CELERY_TASK_HEARTBEAT_URL = os.getenv(
    "ALERT_GROUP_ESCALATION_AUDITOR_CELERY_TASK_HEARTBEAT_URL", None
)

CELERY_BEAT_SCHEDULE_FILENAME = os.getenv("CELERY_BEAT_SCHEDULE_FILENAME", "celerybeat-schedule")

CELERY_BEAT_SCHEDULE = {
    "start_refresh_ical_final_schedules": {
        "task": "apps.schedules.tasks.refresh_ical_files.start_refresh_ical_final_schedules",
        "schedule": crontab(minute=15, hour=0),
        "args": (),
    },
    "start_refresh_ical_files": {
        "task": "apps.schedules.tasks.refresh_ical_files.start_refresh_ical_files",
        "schedule": crontab(minute="*/10"),  # every 10 minutes
        "args": (),
    },
    "start_notify_about_gaps_in_schedule": {
        "task": "apps.schedules.tasks.notify_about_gaps_in_schedule.start_notify_about_gaps_in_schedule",
        "schedule": crontab(minute=1, hour=12, day_of_week="monday"),
        "args": (),
    },
    "start_notify_about_empty_shifts_in_schedule": {
        "task": "apps.schedules.tasks.notify_about_empty_shifts_in_schedule.start_notify_about_empty_shifts_in_schedule",
        "schedule": crontab(minute=0, hour=12, day_of_week="monday"),
        "args": (),
    },
    "populate_slack_usergroups": {
        "task": "apps.slack.tasks.populate_slack_usergroups",
        "schedule": crontab(minute=0, hour=9, day_of_week="monday,wednesday,friday"),
        "args": (),
    },
    "populate_slack_channels": {
        "task": "apps.slack.tasks.populate_slack_channels",
        "schedule": crontab(minute=0, hour=9, day_of_week="tuesday,thursday"),
        "args": (),
    },
    "check_maintenance_finished": {
        "task": "apps.alerts.tasks.maintenance.check_maintenance_finished",
        "schedule": crontab(hour="*", minute=5),
        "args": (),
    },
    "start_sync_organizations": {
        "task": "apps.grafana_plugin.tasks.sync.start_sync_organizations",
        "schedule": crontab(minute="*/30"),
        "args": (),
    },
    "start_cleanup_deleted_integrations": {
        "task": "apps.grafana_plugin.tasks.sync.start_cleanup_deleted_integrations",
        "schedule": crontab(hour="4, 16", minute=35),
        "args": (),
    },
    "start_cleanup_deleted_organizations": {
        "task": "apps.grafana_plugin.tasks.sync.start_cleanup_deleted_organizations",
        "schedule": crontab(hour="*", minute=15),
        "args": (),
    },
    "process_failed_to_invoke_celery_tasks": {
        "task": "apps.base.tasks.process_failed_to_invoke_celery_tasks",
        "schedule": crontab(minute="*/10"),  # every 10 minutes
        "args": (),
    },
    "conditionally_send_going_oncall_push_notifications_for_all_schedules": {
        "task": "apps.mobile_app.tasks.going_oncall_notification.conditionally_send_going_oncall_push_notifications_for_all_schedules",
        "schedule": crontab(minute="*/10"),  # every 10 minutes
    },
    "notify_shift_swap_requests": {
        "task": "apps.mobile_app.tasks.new_shift_swap_request.notify_shift_swap_requests",
        "schedule": crontab(minute="*/{}".format(getenv_integer("NOTIFY_SHIFT_SWAP_REQUESTS_INTERVAL", default=10))),
    },
    "send_shift_swap_request_slack_followups": {
        "task": "apps.schedules.tasks.shift_swaps.slack_followups.send_shift_swap_request_slack_followups",
        "schedule": crontab(minute="*/10"),  # every 10 minutes
    },
    "save_organizations_ids_in_cache": {
        "task": "apps.metrics_exporter.tasks.save_organizations_ids_in_cache",
        "schedule": crontab(minute="*/30"),  # every 30 minutes
        "args": (),
    },
    "check_heartbeats": {
        "task": "apps.heartbeat.tasks.check_heartbeats",
        "schedule": crontab(minute="*/2"),  # every 2 minutes
        "args": (),
    },
}

START_SYNC_ORG_WITH_CHATOPS_PROXY_ENABLED = getenv_boolean("START_SYNC_ORG_WITH_CHATOPS_PROXY_ENABLED", default=False)
if FEATURE_MULTIREGION_ENABLED and START_SYNC_ORG_WITH_CHATOPS_PROXY_ENABLED:
    CELERY_BEAT_SCHEDULE["start_sync_org_with_chatops_proxy"] = {
        "task": "apps.chatops_proxy.tasks.start_sync_org_with_chatops_proxy",
        "schedule": crontab(minute=0, hour=12),  # Execute every day at noon
        "args": (),
    }

if ESCALATION_AUDITOR_ENABLED:
    CELERY_BEAT_SCHEDULE["check_escalations"] = {
        "task": "apps.alerts.tasks.check_escalation_finished.check_escalation_finished_task",
        # the task should be executed a minute or two less than the integration's configured interval
        #
        # ex. if the integration is configured to expect a heartbeat every 15 minutes then this value should be set
        # to something like 13 * 60 (every 13 minutes)
        "schedule": crontab(
            minute="*/{}".format(
                getenv_integer("ALERT_GROUP_ESCALATION_AUDITOR_CELERY_TASK_HEARTBEAT_INTERVAL", default=13)
            )
        ),
        "args": (),
    }
    CELERY_BEAT_SCHEDULE["check_personal_notifications"] = {
        "task": "apps.alerts.tasks.check_escalation_finished.check_personal_notifications_task",
        "schedule": crontab(minute="*/15"),  # every 15 minutes
        "args": (),
    }

INTERNAL_IPS = ["127.0.0.1"]

SELF_IP = os.environ.get("SELF_IP")

SILK_PROFILER_ENABLED = getenv_boolean("SILK_PROFILER_ENABLED", default=False) and not IS_IN_MAINTENANCE_MODE

# django admin panel is required to auth with django silk. Otherwise if silk isn't enabled, we don't need it.
ONCALL_DJANGO_ADMIN_PATH = os.environ.get("ONCALL_DJANGO_ADMIN_PATH", "django-admin") + "/"
ADMIN_ENABLED = SILK_PROFILER_ENABLED

if SILK_PROFILER_ENABLED:
    SILK_PATH = os.environ.get("SILK_PATH", "silk/")
    SILKY_INTERCEPT_PERCENT = getenv_integer("SILKY_INTERCEPT_PERCENT", 100)

    INSTALLED_APPS += ["silk"]
    MIDDLEWARE += ["silk.middleware.SilkyMiddleware"]

    SILKY_AUTHENTICATION = True
    SILKY_AUTHORISATION = True
    SILKY_PYTHON_PROFILER_BINARY = getenv_boolean("SILKY_PYTHON_PROFILER_BINARY", default=False)
    SILKY_PYTHON_PROFILER = True
    SILKY_IGNORE_PATHS = ["/health/", "/ready/"]

    # see the following GitHub issue comment for why the following two settings are set the way they are
    # https://github.com/jazzband/django-silk/issues/265#issuecomment-705482767
    SILKY_MAX_RECORDED_REQUESTS_CHECK_PERCENT = 0.01
    SILKY_MAX_RECORDED_REQUESTS = 100_000

    if "SILKY_PYTHON_PROFILER_RESULT_PATH" in os.environ:
        SILKY_PYTHON_PROFILER_RESULT_PATH = os.environ.get("SILKY_PYTHON_PROFILER_RESULT_PATH")

# Social auth settings
SOCIAL_AUTH_USER_MODEL = "user_management.User"
SOCIAL_AUTH_STRATEGY = "apps.social_auth.live_setting_django_strategy.LiveSettingDjangoStrategy"

# https://python-social-auth.readthedocs.io/en/latest/configuration/settings.html
AUTHENTICATION_BACKENDS = [
    "apps.social_auth.backends.InstallSlackOAuth2V2",
    "apps.social_auth.backends.LoginSlackOAuth2V2",
    "django.contrib.auth.backends.ModelBackend",
    "apps.social_auth.backends.GoogleOAuth2",
]

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ.get("SOCIAL_AUTH_GOOGLE_OAUTH2_KEY")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ.get("SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET")
GOOGLE_OAUTH2_ENABLED = SOCIAL_AUTH_GOOGLE_OAUTH2_KEY is not None and SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET is not None

if GOOGLE_OAUTH2_ENABLED:
    CELERY_BEAT_SCHEDULE["sync_google_calendar_out_of_office_events_for_all_users"] = {
        "task": "apps.google.tasks.sync_out_of_office_calendar_events_for_all_users",
        "schedule": crontab(minute="*/30"),  # every 30 minutes
        "args": (),
    }

# NOTE: for right now we probably only need the calendar.events.readonly scope
# however, if we want to write events back to the user's calendar
# we'll probably need to change this to the calendar.events scope
# (not sure how hard this is to migrate to in the future?)
# https://developers.google.com/identity/protocols/oauth2/scopes#calendar
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = getenv_list(
    "SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE", default=["https://www.googleapis.com/auth/calendar.events.readonly"]
)

SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
SLACK_SIGNING_SECRET_LIVE = os.environ.get("SLACK_SIGNING_SECRET_LIVE", "")

SLACK_CLIENT_OAUTH_ID = os.environ.get("SLACK_CLIENT_OAUTH_ID")
SLACK_CLIENT_OAUTH_SECRET = os.environ.get("SLACK_CLIENT_OAUTH_SECRET")
SLACK_DIRECT_PAGING_SLASH_COMMAND = os.environ.get("SLACK_DIRECT_PAGING_SLASH_COMMAND", "/escalate").lstrip("/")
# it's a root command for unified slack - '/<SLACK_IRM_ROOT_COMMAND> incident new', '/<SLACK_IRM_ROOT_COMMAND> escalate'
SLACK_IRM_ROOT_COMMAND = os.environ.get("SLACK_IRM_ROOT_COMMAND", "/grafana").lstrip("/")

# Controls if slack integration can be installed/uninstalled.
SLACK_INTEGRATION_MAINTENANCE_ENABLED = os.environ.get("SLACK_INTEGRATION_MAINTENANCE_ENABLED", False)

SOCIAL_AUTH_SLACK_LOGIN_KEY = SLACK_CLIENT_OAUTH_ID
SOCIAL_AUTH_SLACK_LOGIN_SECRET = SLACK_CLIENT_OAUTH_SECRET

SOCIAL_AUTH_SETTING_NAME_TO_LIVE_SETTING_NAME = {
    "SOCIAL_AUTH_SLACK_LOGIN_KEY": "SLACK_CLIENT_OAUTH_ID",
    "SOCIAL_AUTH_SLACK_LOGIN_SECRET": "SLACK_CLIENT_OAUTH_SECRET",
    "SOCIAL_AUTH_SLACK_INSTALL_FREE_KEY": "SLACK_CLIENT_OAUTH_ID",
    "SOCIAL_AUTH_SLACK_INSTALL_FREE_SECRET": "SLACK_CLIENT_OAUTH_SECRET",
}
SOCIAL_AUTH_SLACK_INSTALL_FREE_CUSTOM_SCOPE = [
    "bot",
    "chat:write:bot",
    "users:read",
    "users.profile:read",
    "commands",
    "usergroups:read",
]

SOCIAL_AUTH_PIPELINE = (
    "apps.social_auth.pipeline.common.set_user_and_organization_from_request",
    "social_core.pipeline.social_auth.social_details",
    "apps.social_auth.pipeline.slack.connect_user_to_slack",
    "apps.social_auth.pipeline.slack.populate_slack_identities",
    "apps.social_auth.pipeline.slack.delete_slack_auth_token",
)

SOCIAL_AUTH_GOOGLE_OAUTH2_PIPELINE = (
    "apps.social_auth.pipeline.common.set_user_and_organization_from_request",
    "apps.social_auth.pipeline.google.connect_user_to_google",
)

SOCIAL_AUTH_GOOGLE_OAUTH2_DISCONNECT_PIPELINE = (
    "apps.social_auth.pipeline.common.set_user_and_organization_from_request",
    "apps.social_auth.pipeline.google.disconnect_user_google_oauth2_settings",
)

# https://python-social-auth.readthedocs.io/en/latest/use_cases.html#re-prompt-google-oauth2-users-to-refresh-the-refresh-token
# https://developers.google.com/identity/protocols/oauth2/web-server
SOCIAL_AUTH_GOOGLE_OAUTH2_AUTH_EXTRA_ARGUMENTS = {
    # Indicates whether your application can refresh access tokens when the user is not present at the browser.
    # Valid parameter values are online, which is the default value, and offline.
    "access_type": "offline",
    "approval_prompt": "auto",
}

SOCIAL_AUTH_FIELDS_STORED_IN_SESSION: typing.List[str] = []
SOCIAL_AUTH_REDIRECT_IS_HTTPS = getenv_boolean("SOCIAL_AUTH_REDIRECT_IS_HTTPS", default=True)
SOCIAL_AUTH_SLUGIFY_USERNAMES = True

PUBLIC_PRIMARY_KEY_MIN_LENGTH = 12
# excluding (O,0) Result: (25 + 9)^12 combinations
PUBLIC_PRIMARY_KEY_ALLOWED_CHARS = "ABCDEFGHIJKLMNPQRSTUVWXYZ123456789"

AUTH_LINK_TIMEOUT_SECONDS = 300
AUTH_TOKEN_TIMEOUT_SECONDS = 300

SLACK_INSTALL_RETURN_REDIRECT_HOST = os.environ.get("SLACK_INSTALL_RETURN_REDIRECT_HOST", None)

SESSION_COOKIE_DOMAIN = os.environ.get("SESSION_COOKIE_DOMAIN", None)
SESSION_COOKIE_NAME = "oncall_session"

GRAFANA_COM_API_URL = os.environ.get("GRAFANA_COM_API_URL", "https://grafana.com/api/")
GRAFANA_COM_USER_AGENT = "Grafana OnCall"
GRAFANA_COM_API_TOKEN = os.environ.get("GCOM_API_TOKEN", None)
GRAFANA_COM_ADMIN_API_TOKEN = os.environ.get("GRAFANA_COM_ADMIN_API_TOKEN", None)

GRAFANA_API_KEY_NAME = "Grafana OnCall"

EXTRA_MESSAGING_BACKENDS = [
    ("apps.mobile_app.backend.MobileAppBackend", 5),
    ("apps.mobile_app.backend.MobileAppCriticalBackend", 6),
]

# Firebase credentials can be passed as base64 encoded JSON string in GOOGLE_APPLICATION_CREDENTIALS_JSON_BASE64 env variable.
# If it's not passed, firebase_admin will use a file located at GOOGLE_APPLICATION_CREDENTIALS env variable.
credential = None
GOOGLE_APPLICATION_CREDENTIALS_JSON_BASE64 = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON_BASE64", None)
if GOOGLE_APPLICATION_CREDENTIALS_JSON_BASE64:
    credentials_json = json.loads(base64.b64decode(GOOGLE_APPLICATION_CREDENTIALS_JSON_BASE64))
    credential = credentials.Certificate(credentials_json)

# FCM_PROJECT_ID can be different from the project ID in the credentials file.
FCM_PROJECT_ID = os.environ.get("FCM_PROJECT_ID", None)

FCM_RELAY_ENABLED = getenv_boolean("FCM_RELAY_ENABLED", default=False)
FCM_DJANGO_SETTINGS = {
    # an instance of firebase_admin.App to be used as default for all fcm-django requests
    "DEFAULT_FIREBASE_APP": initialize_app(credential=credential, options={"projectId": FCM_PROJECT_ID}),
    "APP_VERBOSE_NAME": "OnCall",
    "ONE_DEVICE_PER_USER": True,
    "DELETE_INACTIVE_DEVICES": True,
    "UPDATE_ON_DUPLICATE_REG_ID": True,
    "USER_MODEL": "user_management.User",
}

MOBILE_APP_GATEWAY_ENABLED = getenv_boolean("MOBILE_APP_GATEWAY_ENABLED", default=False)
GRAFANA_CLOUD_AUTH_API_URL = os.environ.get("GRAFANA_CLOUD_AUTH_API_URL", None)
GRAFANA_CLOUD_AUTH_API_SYSTEM_TOKEN = os.environ.get("GRAFANA_CLOUD_AUTH_API_SYSTEM_TOKEN", None)

SELF_HOSTED_SETTINGS = {
    "STACK_ID": getenv_integer("SELF_HOSTED_STACK_ID", 5),
    "STACK_SLUG": os.environ.get("SELF_HOSTED_STACK_SLUG", "self_hosted_stack"),
    "ORG_ID": 100,
    "ORG_SLUG": os.environ.get("SELF_HOSTED_ORG_SLUG", "self_hosted_org"),
    "ORG_TITLE": os.environ.get("SELF_HOSTED_ORG_TITLE", "Self-Hosted Organization"),
    "REGION_SLUG": os.environ.get("SELF_HOSTED_REGION_SLUG", "self_hosted_region"),
    "GRAFANA_API_URL": os.environ.get("GRAFANA_API_URL", default=None),
    "CLUSTER_SLUG": os.environ.get("SELF_HOSTED_CLUSTER_SLUG", "self_hosted_cluster"),
}

GRAFANA_INCIDENT_STATIC_API_KEY = os.environ.get("GRAFANA_INCIDENT_STATIC_API_KEY", None)

JINJA_TEMPLATE_MAX_LENGTH = os.getenv("JINJA_TEMPLATE_MAX_LENGTH", 50000)
JINJA_RESULT_TITLE_MAX_LENGTH = os.getenv("JINJA_RESULT_TITLE_MAX_LENGTH", 500)
JINJA_RESULT_MAX_LENGTH = os.getenv("JINJA_RESULT_MAX_LENGTH", 50000)

# Log inbound/outbound calls as slow=1 if they exceed threshold
SLOW_THRESHOLD_SECONDS = 2.0

# Email messaging backend
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
EMAIL_PORT = getenv_integer("EMAIL_PORT", 587)
EMAIL_USE_TLS = getenv_boolean("EMAIL_USE_TLS", True)
EMAIL_USE_SSL = getenv_boolean("EMAIL_USE_SSL", False)
EMAIL_FROM_ADDRESS = os.getenv("EMAIL_FROM_ADDRESS")
EMAIL_NOTIFICATIONS_LIMIT = getenv_integer("EMAIL_NOTIFICATIONS_LIMIT", 200)

EMAIL_BACKEND_INTERNAL_ID = 8
if FEATURE_EMAIL_INTEGRATION_ENABLED:
    EXTRA_MESSAGING_BACKENDS += [("apps.email.backend.EmailBackend", EMAIL_BACKEND_INTERNAL_ID)]

# Inbound email settings
INBOUND_EMAIL_ESP = os.getenv("INBOUND_EMAIL_ESP")
INBOUND_EMAIL_DOMAIN = os.getenv("INBOUND_EMAIL_DOMAIN")
INBOUND_EMAIL_WEBHOOK_SECRET = os.getenv("INBOUND_EMAIL_WEBHOOK_SECRET")

INSTALLED_ONCALL_INTEGRATIONS = [
    # Featured
    "config_integrations.grafana_alerting",
    "config_integrations.webhook",
    "config_integrations.alertmanager",
    # Not featured
    "config_integrations.formatted_webhook",
    "config_integrations.kapacitor",
    "config_integrations.elastalert",
    "config_integrations.heartbeat",
    "config_integrations.inbound_email",
    "config_integrations.maintenance",
    "config_integrations.manual",
    "config_integrations.slack_channel",
    "config_integrations.zabbix",
    "config_integrations.direct_paging",
    # Actually it's Grafana 8 integration.
    # users are confused and tries to use to send alerts from external Grafana.
    # So move it closer to the end of the list
    "config_integrations.grafana",
    # Legacy are not shown, ordering isn't important
    "config_integrations.legacy_alertmanager",
    "config_integrations.legacy_grafana_alerting",
]

ADVANCED_WEBHOOK_PRESET = "apps.webhooks.presets.advanced.AdvancedWebhookPreset"
INSTALLED_WEBHOOK_PRESETS = [
    "apps.webhooks.presets.simple.SimpleWebhookPreset",
    ADVANCED_WEBHOOK_PRESET,
]

if IS_OPEN_SOURCE:
    INSTALLED_APPS += ["apps.oss_installation", "apps.zvonok", "apps.exotel"]  # noqa

    CELERY_BEAT_SCHEDULE["send_usage_stats"] = {  # noqa
        "task": "apps.oss_installation.tasks.send_usage_stats_report",
        "schedule": crontab(
            hour=0, minute=randrange(0, 59)
        ),  # Send stats report at a random minute past midnight  # noqa
        "args": (),
    }  # noqa

    CELERY_BEAT_SCHEDULE["send_cloud_heartbeat"] = {  # noqa
        "task": "apps.oss_installation.tasks.send_cloud_heartbeat_task",
        "schedule": crontab(minute="*/3"),  # noqa
        "args": (),
    }  # noqa

    CELERY_BEAT_SCHEDULE["sync_users_with_cloud"] = {  # noqa
        "task": "apps.oss_installation.tasks.sync_users_with_cloud",
        "schedule": crontab(hour="*/12"),  # noqa
        "args": (),
    }  # noqa

# RECAPTCHA_V3 settings
RECAPTCHA_V3_SITE_KEY = os.environ.get("RECAPTCHA_SITE_KEY", default="6LeIPJ8kAAAAAJdUfjO3uUtQtVxsYf93y46mTec1")
RECAPTCHA_V3_SECRET_KEY = os.environ.get("RECAPTCHA_SECRET_KEY", default=None)
RECAPTCHA_V3_ENABLED = os.environ.get("RECAPTCHA_ENABLED", default=False)
RECAPTCHA_V3_HOSTNAME_VALIDATION = os.environ.get("RECAPTCHA_HOSTNAME_VALIDATION", default=False)

MIGRATION_LINTER_OPTIONS = {"exclude_apps": ["social_django", "silk", "fcm_django"]}
# Run migrations linter on each `python manage.py makemigrations`
MIGRATION_LINTER_OVERRIDE_MAKEMIGRATIONS = True

PYROSCOPE_PROFILER_ENABLED = getenv_boolean("PYROSCOPE_PROFILER_ENABLED", default=False)
PYROSCOPE_APPLICATION_NAME = os.getenv("PYROSCOPE_APPLICATION_NAME", "oncall")
PYROSCOPE_SERVER_ADDRESS = os.getenv("PYROSCOPE_SERVER_ADDRESS", "http://pyroscope:4040")
PYROSCOPE_AUTH_TOKEN = os.getenv("PYROSCOPE_AUTH_TOKEN", "")

# map of phone provider alias to importpath.
# Used in get_phone_provider function to dynamically load current provider.
DEFAULT_PHONE_PROVIDER = "twilio"
PHONE_PROVIDERS = {
    "twilio": "apps.twilioapp.phone_provider.TwilioPhoneProvider",
    # "simple": "apps.phone_notifications.simple_phone_provider.SimplePhoneProvider",
}

if IS_OPEN_SOURCE:
    PHONE_PROVIDERS["zvonok"] = "apps.zvonok.phone_provider.ZvonokPhoneProvider"
    PHONE_PROVIDERS["exotel"] = "apps.exotel.phone_provider.ExotelPhoneProvider"

PHONE_PROVIDER = os.environ.get("PHONE_PROVIDER", default=DEFAULT_PHONE_PROVIDER)

ZVONOK_API_KEY = os.getenv("ZVONOK_API_KEY", None)
ZVONOK_CAMPAIGN_ID = os.getenv("ZVONOK_CAMPAIGN_ID", None)
ZVONOK_AUDIO_ID = os.getenv("ZVONOK_AUDIO_ID", None)
ZVONOK_SPEAKER_ID = os.getenv("ZVONOK_SPEAKER_ID", "Salli")
ZVONOK_POSTBACK_CALL_ID = os.getenv("ZVONOK_POSTBACK_CALL_ID", "call_id")
ZVONOK_POSTBACK_CAMPAIGN_ID = os.getenv("ZVONOK_POSTBACK_CAMPAIGN_ID", "campaign_id")
ZVONOK_POSTBACK_STATUS = os.getenv("ZVONOK_POSTBACK_STATUS", "status")
ZVONOK_POSTBACK_USER_CHOICE = os.getenv("ZVONOK_POSTBACK_USER_CHOICE", None)
ZVONOK_POSTBACK_USER_CHOICE_ACK = os.getenv("ZVONOK_POSTBACK_USER_CHOICE_ACK", None)
ZVONOK_VERIFICATION_CAMPAIGN_ID = os.getenv("ZVONOK_VERIFICATION_CAMPAIGN_ID", None)

EXOTEL_ACCOUNT_SID = os.getenv("EXOTEL_ACCOUNT_SID", None)
EXOTEL_API_KEY = os.getenv("EXOTEL_API_KEY", None)
EXOTEL_API_TOKEN = os.getenv("EXOTEL_API_TOKEN", None)
EXOTEL_APP_ID = os.getenv("EXOTEL_APP_ID", None)
EXOTEL_CALLER_ID = os.getenv("EXOTEL_CALLER_ID", None)
EXOTEL_SMS_SENDER_ID = os.getenv("EXOTEL_SMS_SENDER_ID", None)
EXOTEL_SMS_VERIFICATION_TEMPLATE = os.getenv("EXOTEL_SMS_VERIFICATION_TEMPLATE", None)
EXOTEL_SMS_DLT_ENTITY_ID = os.getenv("EXOTEL_SMS_DLT_ENTITY_ID", None)

DETACHED_INTEGRATIONS_SERVER = getenv_boolean("DETACHED_INTEGRATIONS_SERVER", default=False)

ACKNOWLEDGE_REMINDER_TASK_EXPIRY_DAYS = os.environ.get("ACKNOWLEDGE_REMINDER_TASK_EXPIRY_DAYS", default=14)
