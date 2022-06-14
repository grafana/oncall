import os
from random import randrange

from celery.schedules import crontab

from common.utils import getenv_boolean

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

ALLOWED_HOSTS = [item.strip() for item in os.environ.get("ALLOWED_HOSTS", "*").split(",")]

# TODO: update link to up-to-date docs
DOCS_URL = "https://grafana.com/docs/grafana-cloud/oncall/"

# Settings of running OnCall instance.
BASE_URL = os.environ.get("BASE_URL")  # Root URL of OnCall backend

# Feature toggles
FEATURE_LIVE_SETTINGS_ENABLED = getenv_boolean("FEATURE_LIVE_SETTINGS_ENABLED", default=True)
FEATURE_TELEGRAM_INTEGRATION_ENABLED = getenv_boolean("FEATURE_TELEGRAM_INTEGRATION_ENABLED", default=True)
FEATURE_EMAIL_INTEGRATION_ENABLED = getenv_boolean("FEATURE_EMAIL_INTEGRATION_ENABLED", default=False)
FEATURE_SLACK_INTEGRATION_ENABLED = getenv_boolean("FEATURE_SLACK_INTEGRATION_ENABLED", default=True)
GRAFANA_CLOUD_ONCALL_HEARTBEAT_ENABLED = getenv_boolean("GRAFANA_CLOUD_ONCALL_HEARTBEAT_ENABLED", default=True)
GRAFANA_CLOUD_NOTIFICATIONS_ENABLED = getenv_boolean("GRAFANA_CLOUD_NOTIFICATIONS_ENABLED", default=True)

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.environ.get("TWILIO_NUMBER")
TWILIO_VERIFY_SERVICE_SID = os.environ.get("TWILIO_VERIFY_SERVICE_SID")

TELEGRAM_WEBHOOK_HOST = os.environ.get("TELEGRAM_WEBHOOK_HOST", BASE_URL)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

os.environ.setdefault("MYSQL_PASSWORD", "empty")
os.environ.setdefault("RABBIT_URI", "empty")

# For Sending email
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.environ.get("SENDGRID_FROM_EMAIL")

# For Inbound email
SENDGRID_SECRET_KEY = os.environ.get("SENDGRID_SECRET_KEY")
SENDGRID_INBOUND_EMAIL_DOMAIN = os.environ.get("SENDGRID_INBOUND_EMAIL_DOMAIN")

# For Grafana Cloud integration
GRAFANA_CLOUD_ONCALL_API_URL = os.environ.get("GRAFANA_CLOUD_ONCALL_API_URL", "https://a-prod-us-central-0.grafana.net")
GRAFANA_CLOUD_ONCALL_TOKEN = os.environ.get("GRAFANA_CLOUD_ONCALL_TOKEN", None)

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
    "apps.slack",
    "apps.telegram",
    "apps.twilioapp",
    "apps.api",
    "apps.api_for_grafana_incident",
    "apps.base",
    # "apps.sendgridapp",  TODO: restore email notifications
    "apps.auth_token",
    "apps.public_api",
    "apps.grafana_plugin",
    "apps.grafana_plugin_management",
    "apps.migration_tool",
    "django_celery_results",
    "corsheaders",
    "debug_toolbar",
    "social_django",
    "polymorphic",
    "push_notifications",
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
]

LOG_REQUEST_ID_HEADER = "HTTP_X_CLOUD_TRACE_CONTEXT"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"request_id": {"()": "log_request_id.filters.RequestIDFilter"}},
    "formatters": {
        "standard": {"format": "source=engine:app google_trace_id=%(request_id)s logger=%(name)s %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["request_id"],
            "formatter": "standard",
        },
    },
    "loggers": {
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

STATIC_URL = "/static/"
STATIC_ROOT = "./static/"

CELERY_BROKER_URL = "amqp://rabbitmq:rabbitmq@localhost:5672"

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
    "process_failed_to_invoke_celery_tasks": {
        "task": "apps.base.tasks.process_failed_to_invoke_celery_tasks",
        "schedule": 60 * 10,
        "args": (),
    },
}

INTERNAL_IPS = ["127.0.0.1"]

SELF_IP = os.environ.get("SELF_IP")

SILK_PATH = os.environ.get("SILK_PATH", "silk/")
SILKY_AUTHENTICATION = True
SILKY_AUTHORISATION = True
SILKY_META = True
SILKY_INTERCEPT_PERCENT = 1
SILKY_MAX_RECORDED_REQUESTS = 10**4

INSTALLED_APPS += ["silk"]
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

SOCIAL_AUTH_SLACK_LOGIN_KEY = SLACK_CLIENT_OAUTH_ID
SOCIAL_AUTH_SLACK_LOGIN_SECRET = SLACK_CLIENT_OAUTH_SECRET

SOCIAL_AUTH_SETTING_NAME_TO_LIVE_SETTING_NAME = {
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

MOBILE_APP_PUSH_NOTIFICATIONS_ENABLED = getenv_boolean("MOBILE_APP_PUSH_NOTIFICATIONS_ENABLED", default=False)

PUSH_NOTIFICATIONS_SETTINGS = {
    "APNS_AUTH_KEY_PATH": os.environ.get("APNS_AUTH_KEY_PATH", None),
    "APNS_TOPIC": os.environ.get("APNS_TOPIC", None),
    "APNS_AUTH_KEY_ID": os.environ.get("APNS_AUTH_KEY_ID", None),
    "APNS_TEAM_ID": os.environ.get("APNS_TEAM_ID", None),
    "APNS_USE_SANDBOX": True,
    "USER_MODEL": "user_management.User",
}

SELF_HOSTED_SETTINGS = {
    "STACK_ID": 5,
    "STACK_SLUG": "self_hosted_stack",
    "ORG_ID": 100,
    "ORG_SLUG": "self_hosted_org",
    "ORG_TITLE": "Self-Hosted Organization",
}

GRAFANA_INCIDENT_STATIC_API_KEY = os.environ.get("GRAFANA_INCIDENT_STATIC_API_KEY", None)

DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880

# Log inbound/outbound calls as slow=1 if they exceed threshold
SLOW_THRESHOLD_SECONDS = 2.0

FEATURE_EXTRA_MESSAGING_BACKENDS_ENABLED = getenv_boolean("FEATURE_EXTRA_MESSAGING_BACKENDS_ENABLED", default=False)
EXTRA_MESSAGING_BACKENDS = []

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
