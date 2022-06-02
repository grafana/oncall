import os

import celery
from celery.app.log import TaskFormatter

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.prod")

from django.db import connection  # noqa: E402

connection.cursor()
from celery import Celery  # noqa: E402

app = Celery("proj")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


# This task is required for tests with celery, see:
# https://stackoverflow.com/questions/46530784/make-django-test-case-database-visible-to-celery
@app.task(name="celery.ping")
def ping():
    # type: () -> str
    """Simple task that just returns 'pong'."""
    return "pong"


@celery.signals.after_setup_logger.connect
@celery.signals.after_setup_task_logger.connect
def on_after_setup_logger(logger, **kwargs):
    for handler in logger.handlers:
        handler.setFormatter(
            TaskFormatter(
                "%(asctime)s source=engine:celery task_id=%(task_id)s task_name=%(task_name)s name=%(name)s level=%(levelname)s %(message)s"
            )
        )
