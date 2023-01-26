import os
from random import randrange

from celery.schedules import crontab

from common.utils import getenv_boolean, getenv_integer

VERSION = "dev-oss"
# Indicates if instance is OSS installation.
# It is needed to plug-in oss application and urls.
OSS_INSTALLATION = getenv_boolean("GRAFANA_ONCALL_OSS_INSTALLATION", True)
SEND_ANONYMOUS_USAGE_STATS = getenv_boolean("SEND_ANONYMOUS_USAGE_STATS", default=True)

# License is OpenSource or Cloud
OPEN_SOURCE_LICENSE_NAME = "OpenSource"
CLOUD_LICENSE_NAME = "Cloud"
LICENSE = os.environ.get("ONCALL_LICENSE", default=OPEN_SOURCE_LICENSE_NAME)

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

# TODO: update link to up-to-date docs
DOCS_URL = "https://grafana.com/docs/grafana-cloud/oncall/"

# Settings of running OnCall instance.
BASE_URL = os.environ.get("BASE_URL")  # Root URL of OnCall backend

# Feature toggles
FEATURE_LIVE_SETTINGS_ENABLED = getenv_boolean("FEATURE_LIVE_SETTINGS_ENABLED", default=True)
FEATURE_TELEGRAM_INTEGRATION_ENABLED = getenv_boolean("FEATURE_TELEGRAM_INTEGRATION_ENABLED", default=True)
FEATURE_EMAIL_INTEGRATION_ENABLED = getenv_boolean("FEATURE_EMAIL_INTEGRATION_ENABLED", default=True)
FEATURE_SLACK_INTEGRATION_ENABLED = getenv_boolean("FEATURE_SLACK_INTEGRATION_ENABLED", default=True)
FEATURE_MOBILE_APP_INTEGRATION_ENABLED = getenv_boolean("FEATURE_MOBILE_APP_INTEGRATION_ENABLED", default=False)
FEATURE_WEB_SCHEDULES_ENABLED = getenv_boolean("FEATURE_WEB_SCHEDULES_ENABLED", default=False)
FEATURE_MULTIREGION_ENABLED = getenv_boolean("FEATURE_MULTIREGION_ENABLED", default=False)
GRAFANA_CLOUD_ONCALL_HEARTBEAT_ENABLED = getenv_boolean("GRAFANA_CLOUD_ONCALL_HEARTBEAT_ENABLED", default=True)
GRAFANA_CLOUD_NOTIFICATIONS_ENABLED = getenv_boolean("GRAFANA_CLOUD_NOTIFICATIONS_ENABLED", default=True)

TWILIO_API_KEY_SID = os.environ.get("TWILIO_API_KEY_SID")
TWILIO_API_KEY_SECRET = os.environ.get("TWILIO_API_KEY_SECRET")
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.environ.get("TWILIO_NUMBER")
TWILIO_VERIFY_SERVICE_SID = os.environ.get("TWILIO_VERIFY_SERVICE_SID")

TELEGRAM_WEBHOOK_HOST = os.environ.get("TELEGRAM_WEBHOOK_HOST", BASE_URL)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# For Grafana Cloud integration
GRAFANA_CLOUD_ONCALL_API_URL = os.environ.get(
    "GRAFANA_CLOUD_ONCALL_API_URL", "https://oncall-prod-us-central-0.grafana.net/oncall"
)
GRAFANA_CLOUD_ONCALL_TOKEN = os.environ.get("GRAFANA_CLOUD_ONCALL_TOKEN", None)

# Outgoing webhook settings
DANGEROUS_WEBHOOKS_ENABLED = getenv_boolean("DANGEROUS_WEBHOOKS_ENABLED", default=False)

# Multiregion settings
ONCALL_GATEWAY_URL = os.environ.get("ONCALL_GATEWAY_URL")
ONCALL_GATEWAY_API_TOKEN = os.environ.get("ONCALL_GATEWAY_API_TOKEN")
ONCALL_BACKEND_REGION = os.environ.get("ONCALL_BACKEND_REGION")


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

DATABASE_NAME = os.getenv("DATABASE_NAME") or os.getenv("MYSQL_DB_NAME")
DATABASE_USER = os.getenv("DATABASE_USER") or os.getenv("MYSQL_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD") or os.getenv("MYSQL_PASSWORD")
DATABASE_HOST = os.getenv("DATABASE_HOST") or os.getenv("MYSQL_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT") or os.getenv("MYSQL_PORT")

DATABASE_TYPE = os.getenv("DATABASE_TYPE", DatabaseTypes.MYSQL).lower()
assert DATABASE_TYPE in {DatabaseTypes.MYSQL, DatabaseTypes.POSTGRESQL, DatabaseTypes.SQLITE3}

DATABASE_ENGINE = f"django.db.backends.{DATABASE_TYPE}"

DATABASE_CONFIGS = {
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
        "OPTIONS": {
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
    },
}

DATABASES = {
    "default": DATABASE_CONFIGS[DATABASE_TYPE],
}
if DATABASE_TYPE == DatabaseTypes.MYSQL:
    # Workaround to use pymysql instead of mysqlclient
    import pymysql

    pymysql.install_as_MySQLdb()

# Redis
REDIS_USERNAME = os.getenv("REDIS_USERNAME", "")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)
REDIS_PROTOCOL = os.getenv("REDIS_PROTOCOL", "redis")

REDIS_URI = os.getenv("REDIS_URI")
if not REDIS_URI:
    REDIS_URI = f"{REDIS_PROTOCOL}://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}"

# Cache
CACHES = {
    "default": {
        "BACKEND": "redis_cache.RedisCache",
        "LOCATION": [
            REDIS_URI,
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
    "ordered_model",
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
    "corsheaders",
    "debug_toolbar",
    "social_django",
    "polymorphic",
    "fcm_django",
]

REST_FRAMEWORK = {
    "DEFAULT_PARSER_CLASSES": (
        "engine.parsers.JSONParser",
        "engine.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": [],
}

MIDDLEWARE = [
    "log_request_id.middleware.RequestIDMiddleware",
    "engine.middlewares.RequestTimeLoggingMiddleware",
    "engine.middlewares.BanAlertConsumptionBasedOnSettingsMiddleware",
    "engine.middlewares.RequestBodyReadingMiddleware",
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

LOG_REQUEST_ID_HEADER = "HTTP_X_CLOUD_TRACE_CONTEXT"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"request_id": {"()": "log_request_id.filters.RequestIDFilter"}},
    "formatters": {
        "standard": {"format": "source=engine:app google_trace_id=%(request_id)s logger=%(name)s %(message)s"},
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

ROOT_URLCONF = "engine.urls"

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

USE_L10N = True

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

CELERY_BEAT_SCHEDULE = {
    "restore_heartbeat_tasks": {
        "task": "apps.heartbeat.tasks.restore_heartbeat_tasks",
        "schedule": 10 * 60,
        "args": (),
    },
    "check_escalations": {
        "task": "apps.alerts.tasks.check_escalation_finished.check_escalation_finished_task",
        "schedule": 10 * 60,
        "args": (),
    },
    "start_refresh_ical_files": {
        "task": "apps.schedules.tasks.refresh_ical_files.start_refresh_ical_files",
        "schedule": 10 * 60,
        "args": (),
    },
    "start_notify_about_gaps_in_schedule": {
        "task": "apps.schedules.tasks.notify_about_gaps_in_schedule.start_notify_about_gaps_in_schedule",
        "schedule": crontab(minute=1, hour=12, day_of_week="monday"),
        "args": (),
    },
    "start_check_gaps_in_schedule": {
        "task": "apps.schedules.tasks.notify_about_gaps_in_schedule.start_check_gaps_in_schedule",
        "schedule": crontab(minute=0, hour=0),
        "args": (),
    },
    "start_notify_about_empty_shifts_in_schedule": {
        "task": "apps.schedules.tasks.notify_about_empty_shifts_in_schedule.start_notify_about_empty_shifts_in_schedule",
        "schedule": crontab(minute=0, hour=12, day_of_week="monday"),
        "args": (),
    },
    "start_check_empty_shifts_in_schedule": {
        "task": "apps.schedules.tasks.notify_about_empty_shifts_in_schedule.start_check_empty_shifts_in_schedule",
        "schedule": crontab(minute=0, hour=0),
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
    "start_cleanup_deleted_organizations": {
        "task": "apps.grafana_plugin.tasks.sync.start_cleanup_deleted_organizations",
        "schedule": crontab(hour="*", minute=15),
        "args": (),
    },
    "process_failed_to_invoke_celery_tasks": {
        "task": "apps.base.tasks.process_failed_to_invoke_celery_tasks",
        "schedule": 60 * 10,
        "args": (),
    },
}

INTERNAL_IPS = ["127.0.0.1"]

SELF_IP = os.environ.get("SELF_IP")

SILK_PROFILER_ENABLED = getenv_boolean("SILK_PROFILER_ENABLED", default=False)
if SILK_PROFILER_ENABLED:
    SILK_PATH = os.environ.get("SILK_PATH", "silk/")
    SILKY_INTERCEPT_PERCENT = getenv_integer("SILKY_INTERCEPT_PERCENT", 100)

    INSTALLED_APPS += ["silk"]
    MIDDLEWARE += ["silk.middleware.SilkyMiddleware"]

    SILKY_AUTHENTICATION = True
    SILKY_AUTHORISATION = True
    SILKY_PYTHON_PROFILER_BINARY = getenv_boolean("SILKY_PYTHON_PROFILER_BINARY", default=False)
    SILKY_MAX_RECORDED_REQUESTS = 10**4
    SILKY_PYTHON_PROFILER = True
    SILKY_IGNORE_PATHS = ["/health/", "/ready/"]
    if "SILKY_PYTHON_PROFILER_RESULT_PATH" in os.environ:
        SILKY_PYTHON_PROFILER_RESULT_PATH = os.environ.get("SILKY_PYTHON_PROFILER_RESULT_PATH")

# get ONCALL_DJANGO_ADMIN_PATH from env and add trailing / to it
ONCALL_DJANGO_ADMIN_PATH = os.environ.get("ONCALL_DJANGO_ADMIN_PATH", "django-admin") + "/"

ADMIN_SITE_HEADER = "OnCall Admin Panel"

# Social auth settings
SOCIAL_AUTH_USER_MODEL = "user_management.User"
SOCIAL_AUTH_STRATEGY = "apps.social_auth.live_setting_django_strategy.LiveSettingDjangoStrategy"

# https://python-social-auth.readthedocs.io/en/latest/configuration/settings.html
AUTHENTICATION_BACKENDS = [
    "apps.social_auth.backends.InstallSlackOAuth2V2",
    "apps.social_auth.backends.LoginSlackOAuth2V2",
    "django.contrib.auth.backends.ModelBackend",
]

SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
SLACK_SIGNING_SECRET_LIVE = os.environ.get("SLACK_SIGNING_SECRET_LIVE", "")

SLACK_CLIENT_OAUTH_ID = os.environ.get("SLACK_CLIENT_OAUTH_ID")
SLACK_CLIENT_OAUTH_SECRET = os.environ.get("SLACK_CLIENT_OAUTH_SECRET")

SLACK_SLASH_COMMAND_NAME = os.environ.get("SLACK_SLASH_COMMAND_NAME", "/oncall")
SLACK_DIRECT_PAGING_SLASH_COMMAND = os.environ.get("SLACK_DIRECT_PAGING_SLASH_COMMAND", "/escalate")

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
    "apps.social_auth.pipeline.set_user_and_organization_from_request",
    "social_core.pipeline.social_auth.social_details",
    "apps.social_auth.pipeline.connect_user_to_slack",
    "apps.social_auth.pipeline.populate_slack_identities",
    "apps.social_auth.pipeline.delete_slack_auth_token",
)

SOCIAL_AUTH_FIELDS_STORED_IN_SESSION = []
SOCIAL_AUTH_REDIRECT_IS_HTTPS = getenv_boolean("SOCIAL_AUTH_REDIRECT_IS_HTTPS", default=True)
SOCIAL_AUTH_SLUGIFY_USERNAMES = True

FEATURE_CAPTCHA_ENABLED = getenv_boolean("FEATURE_CAPTCHA_ENABLED", default=False)
RECAPTCHA_SECRET_KEY = os.environ.get("RECAPTCHA_SECRET_KEY")

PUBLIC_PRIMARY_KEY_MIN_LENGTH = 12
# excluding (O,0) Result: (25 + 9)^12 combinations
PUBLIC_PRIMARY_KEY_ALLOWED_CHARS = "ABCDEFGHIJKLMNPQRSTUVWXYZ123456789"

AUTH_LINK_TIMEOUT_SECONDS = 300
SLACK_AUTH_TOKEN_TIMEOUT_SECONDS = 300

SLACK_INSTALL_RETURN_REDIRECT_HOST = os.environ.get("SLACK_INSTALL_RETURN_REDIRECT_HOST", None)

SESSION_COOKIE_DOMAIN = os.environ.get("SESSION_COOKIE_DOMAIN", None)
SESSION_COOKIE_NAME = "oncall_session"

GRAFANA_COM_API_URL = os.environ.get("GRAFANA_COM_API_URL", "https://grafana.com/api/")
GRAFANA_COM_USER_AGENT = "Grafana OnCall"
GRAFANA_COM_API_TOKEN = os.environ.get("GCOM_API_TOKEN", None)
GRAFANA_COM_ADMIN_API_TOKEN = os.environ.get("GRAFANA_COM_ADMIN_API_TOKEN", None)

GRAFANA_API_KEY_NAME = "Grafana OnCall"

EXTRA_MESSAGING_BACKENDS = []
if FEATURE_MOBILE_APP_INTEGRATION_ENABLED:
    from firebase_admin import initialize_app

    EXTRA_MESSAGING_BACKENDS += [
        ("apps.mobile_app.backend.MobileAppBackend", 5),
        ("apps.mobile_app.backend.MobileAppCriticalBackend", 6),
    ]

    FIREBASE_APP = initialize_app(options={"projectId": os.environ.get("FCM_PROJECT_ID", None)})

FCM_RELAY_ENABLED = getenv_boolean("FCM_RELAY_ENABLED", default=False)
FCM_DJANGO_SETTINGS = {
    # an instance of firebase_admin.App to be used as default for all fcm-django requests
    # default: None (the default Firebase app)
    "DEFAULT_FIREBASE_APP": None,
    "APP_VERBOSE_NAME": "OnCall",
    "ONE_DEVICE_PER_USER": True,
    "DELETE_INACTIVE_DEVICES": False,
    "UPDATE_ON_DUPLICATE_REG_ID": True,
    "USER_MODEL": "user_management.User",
}

SELF_HOSTED_SETTINGS = {
    "STACK_ID": 5,
    "STACK_SLUG": "self_hosted_stack",
    "ORG_ID": 100,
    "ORG_SLUG": "self_hosted_org",
    "ORG_TITLE": "Self-Hosted Organization",
    "REGION_SLUG": "self_hosted_region",
    "GRAFANA_API_URL": os.environ.get("GRAFANA_API_URL", default=None),
}

GRAFANA_INCIDENT_STATIC_API_KEY = os.environ.get("GRAFANA_INCIDENT_STATIC_API_KEY", None)

DATA_UPLOAD_MAX_MEMORY_SIZE = getenv_integer("DATA_UPLOAD_MAX_MEMORY_SIZE", 1_048_576)  # 1mb by default
JINJA_TEMPLATE_MAX_LENGTH = 50000
JINJA_RESULT_TITLE_MAX_LENGTH = 500
JINJA_RESULT_MAX_LENGTH = 50000

# Log inbound/outbound calls as slow=1 if they exceed threshold
SLOW_THRESHOLD_SECONDS = 2.0

# Email messaging backend
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
EMAIL_PORT = getenv_integer("EMAIL_PORT", 587)
EMAIL_USE_TLS = getenv_boolean("EMAIL_USE_TLS", True)
EMAIL_FROM_ADDRESS = os.getenv("EMAIL_FROM_ADDRESS")

if FEATURE_EMAIL_INTEGRATION_ENABLED:
    EXTRA_MESSAGING_BACKENDS += [("apps.email.backend.EmailBackend", 8)]

INSTALLED_ONCALL_INTEGRATIONS = [
    "config_integrations.alertmanager",
    "config_integrations.grafana",
    "config_integrations.grafana_alerting",
    "config_integrations.formatted_webhook",
    "config_integrations.webhook",
    "config_integrations.kapacitor",
    "config_integrations.elastalert",
    "config_integrations.heartbeat",
    "config_integrations.inbound_email",
    "config_integrations.maintenance",
    "config_integrations.manual",
    "config_integrations.slack_channel",
    "config_integrations.zabbix",
    "config_integrations.direct_paging",
]

if OSS_INSTALLATION:
    INSTALLED_APPS += ["apps.oss_installation"]  # noqa

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

PYROSCOPE_PROFILER_ENABLED = getenv_boolean("PYROSCOPE_PROFILER_ENABLED", default=False)
if PYROSCOPE_PROFILER_ENABLED:
    import pyroscope

    pyroscope.configure(
        application_name=os.getenv("PYROSCOPE_APPLICATION_NAME", "oncall"),
        server_address=os.getenv("PYROSCOPE_SERVER_ADDRESS", "http://pyroscope:4040"),
        auth_token=os.getenv("PYROSCOPE_AUTH_TOKEN", ""),
        detect_subprocesses=True,
        tags={
            "celery_worker": os.getenv("CELERY_WORKER_QUEUE", None),
        },
    )
