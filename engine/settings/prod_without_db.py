import os

from . import celery_task_routes
from .base import *  # noqa: F401, F403

try:
    import uwsgi
    from prometheus_client import multiprocess

    def on_uwsgi_worker_exit():
        multiprocess.mark_process_dead(os.getpid())

        uwsgi.atexit = on_uwsgi_worker_exit

except ModuleNotFoundError:
    # Only works under uwsgi web server environment
    pass


SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
SLACK_SIGNING_SECRET_LIVE = os.environ.get("SLACK_SIGNING_SECRET_LIVE", "")


STATICFILES_DIRS = [
    "/etc/app/static",
]
STATIC_ROOT = "./collected_static/"

DEBUG = False

SECURE_SSL_REDIRECT = True
SECURE_REDIRECT_EXEMPT = [
    "^health/",
    "^health",
    "^ready/",
    "^ready",
    "^startupprobe/",
    "^startupprobe",
    "^ready_health_check/",
    "^ready_health_check",
    "^live_health_check/",
    "^live_health_check",
    "^django-prometheus/metrics",
    "^django-prometheus/metrics/",
]
SECURE_HSTS_SECONDS = 360000

CELERY_TASK_ROUTES = celery_task_routes.CELERY_TASK_ROUTES

REST_FRAMEWORK = {
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}
