from django.urls import re_path

from .views import MetricsExporterView

urlpatterns = [
    re_path(r"^/?$", MetricsExporterView.as_view(), name="metrics-exporter"),
]
