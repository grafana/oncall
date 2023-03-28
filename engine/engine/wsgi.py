"""
WSGI config for engine project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os

from django.conf import settings
from django.core.wsgi import get_wsgi_application
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.pymysql import PyMySQLInstrumentor
from opentelemetry.instrumentation.wsgi import OpenTelemetryMiddleware
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from whitenoise import WhiteNoise

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.prod")

application = get_wsgi_application()
application = WhiteNoise(application)

if settings.OTEL_TRACING_ENABLED and settings.OTEL_EXPORTER_OTLP_ENDPOINT:
    try:
        from uwsgidecorators import postfork

        application = OpenTelemetryMiddleware(application)

        @postfork
        def init_tracing():
            trace.set_tracer_provider(TracerProvider())
            span_processor = BatchSpanProcessor(OTLPSpanExporter())
            trace.get_tracer_provider().add_span_processor(span_processor)
            PyMySQLInstrumentor().instrument()

    except ModuleNotFoundError:
        # Only works under uwsgi web server environment
        pass

if settings.PYROSCOPE_PROFILER_ENABLED:
    try:
        import pyroscope
        from uwsgidecorators import postfork

        @postfork
        def init_pyroscope():
            pyroscope.configure(
                application_name=settings.PYROSCOPE_APPLICATION_NAME,
                server_address=settings.PYROSCOPE_SERVER_ADDRESS,
                auth_token=settings.PYROSCOPE_AUTH_TOKEN,
                detect_subprocesses=True,
                tags={"type": "uwsgi"},
            )

    except ModuleNotFoundError:
        # Only works under uwsgi web server environment
        pass
