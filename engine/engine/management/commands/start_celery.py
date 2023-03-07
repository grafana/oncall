import shlex
import subprocess

from django.core.management.base import BaseCommand
from django.utils import autoreload

WORKER_ID = 0


def restart_celery(*args, **kwargs):
    global WORKER_ID
    kill_worker_cmd = "celery -A engine control shutdown"
    subprocess.call(shlex.split(kill_worker_cmd))
    start_worker_cmd = "celery -A engine worker -l info --concurrency=3 -Q celery,retry -n {}".format(WORKER_ID)
    subprocess.call(shlex.split(start_worker_cmd))
    WORKER_ID = 1 + WORKER_ID


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write("Starting celery worker with autoreload...")
        autoreload.run_with_reloader(restart_celery, args=None, kwargs=None)
