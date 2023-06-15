from django.urls import path

from .views import MetricsExporterView

urlpatterns = [
    path("", MetricsExporterView.as_view(), name="metrics-exporter"),
]
