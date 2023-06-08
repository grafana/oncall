import os
import shlex
import subprocess

from django.core.management.base import BaseCommand
from django.utils import autoreload

from common.utils import getenv_boolean

WORKER_ID = 0


def restart_celery(*args, **kwargs):
    global WORKER_ID
    kill_worker_cmd = "celery -A engine control shutdown"
    subprocess.call(shlex.split(kill_worker_cmd))

    queues = os.environ.get("CELERY_WORKER_QUEUE", "celery,retry")
    max_tasks_per_child = os.environ.get("CELERY_WORKER_MAX_TASKS_PER_CHILD", 100)
    concurrency = os.environ.get("CELERY_WORKER_CONCURRENCY", 3)
    log_level = "debug" if getenv_boolean("CELERY_WORKER_DEBUG_LOGS", False) else "info"

    celery_args = f"-A engine worker -l {log_level} --concurrency={concurrency} -Q {queues} --max-tasks-per-child={max_tasks_per_child} -n {WORKER_ID}"

    if getenv_boolean("CELERY_WORKER_BEAT_ENABLED", False):
        celery_args += " --beat"

    subprocess.call(shlex.split(f"celery {celery_args}"))
    WORKER_ID = 1 + WORKER_ID


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write("Starting celery worker with autoreload...")
        autoreload.run_with_reloader(restart_celery, args=None, kwargs=None)
