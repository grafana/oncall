from django.apps import AppConfig


class MetricsExporterConfig(AppConfig):
    name = "apps.metrics_exporter"

    def ready(self):
        from . import signals  # noqa: F401
