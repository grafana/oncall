#!/usr/bin/env python
import os
import sys

from django.conf import settings
from opentelemetry import trace
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.dev")
    if settings.OTEL_TRACING_ENABLED:
        # Set up tracing and logging instrumentation under manage.ru runserver command.
        # It's used to provide simple way to test tracing locally.
        trace.set_tracer_provider(TracerProvider())
        span_processor = SimpleSpanProcessor(ConsoleSpanExporter())  # Log spans to console to simplify local setup
        trace.get_tracer_provider().add_span_processor(span_processor)
        # DjangoInstrumentor instruments incoming requests and starts root span.
        # It's used instead of wsgi middleware in local setup. Not sure if it should be used in prod
        DjangoInstrumentor().instrument()
        LoggingInstrumentor().instrument()  # Instrument logs to add trace_id to log lines
        RequestsInstrumentor().instrument()  # Instrument requests to instrument downstream calls
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
