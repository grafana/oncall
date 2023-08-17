import logging
import os
import time

import celery
from celery import Celery
from celery.app.log import TaskFormatter
from celery.utils.debug import memdump, sample_mem
from celery.utils.log import get_task_logger
from django.conf import settings
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.pymysql import PyMySQLInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.prod")

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


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
                "%(asctime)s source=engine:celery worker=%(processName)s task_id=%(task_id)s task_name=%(task_name)s name=%(name)s level=%(levelname)s %(message)s"
            )
        )


@celery.signals.worker_ready.connect
def on_worker_ready(*args, **kwargs):
    from apps.telegram.tasks import register_telegram_webhook

    if not settings.FEATURE_TELEGRAM_LONG_POLLING_ENABLED:
        register_telegram_webhook.delay()


if settings.OTEL_TRACING_ENABLED and settings.OTEL_EXPORTER_OTLP_ENDPOINT:

    @celery.signals.worker_process_init.connect(weak=False)
    def init_celery_tracing(*args, **kwargs):
        trace.set_tracer_provider(TracerProvider())
        span_processor = BatchSpanProcessor(OTLPSpanExporter())
        trace.get_tracer_provider().add_span_processor(span_processor)
        PyMySQLInstrumentor().instrument()
        CeleryInstrumentor().instrument()


if settings.DEBUG_CELERY_TASKS_PROFILING:

    @celery.signals.task_prerun.connect
    def start_task_timer(task_id=None, task=None, *a, **kw):
        logger.info("started: {} of {} with cpu={} at {}".format(task_id, task.name, time.perf_counter(), time.time()))
        sample_mem()

    @celery.signals.task_postrun.connect
    def finish_task_timer(task_id=None, task=None, *a, **kw):
        logger.info("ended: {} of {} with cpu={} at {}".format(task_id, task.name, time.perf_counter(), time.time()))
        sample_mem()
        memdump()


if settings.PYROSCOPE_PROFILER_ENABLED:

    @celery.signals.worker_process_init.connect(weak=False)
    def init_pyroscope(*args, **kwargs):
        import pyroscope

        pyroscope.configure(
            application_name=settings.PYROSCOPE_APPLICATION_NAME,
            server_address=settings.PYROSCOPE_SERVER_ADDRESS,
            auth_token=settings.PYROSCOPE_AUTH_TOKEN,
            detect_subprocesses=True,  # detect subprocesses started by the main process; default is False
            tags={"type": "celery", "celery_worker": os.environ.get("CELERY_WORKER_QUEUE", "no_queue_specified")},
        )
