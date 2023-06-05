from django.conf import settings
from django.http import HttpResponse
from prometheus_client import generate_latest
from rest_framework.views import APIView

from .metrics_collectors import application_metrics_registry


class MetricsExporterView(APIView):
    def get(self, request):
        authorization = request.headers.get("Authorization")
        if settings.PROMETHEUS_EXPORTER_SECRET and authorization != settings.PROMETHEUS_EXPORTER_SECRET:
            # unauthorized
            return HttpResponse(status=401)

        result = generate_latest(application_metrics_registry).decode("utf-8")
        return HttpResponse(result, content_type="text/plain; version=0.0.4; charset=utf-8")
