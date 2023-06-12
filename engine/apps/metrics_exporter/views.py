import re

from django.conf import settings
from django.http import HttpResponse
from prometheus_client import generate_latest
from rest_framework.views import APIView

from .metrics_collectors import application_metrics_registry

RE_AUTH_TOKEN = re.compile(r"^[Bb]earer\s{1}(.+)$")


class MetricsExporterView(APIView):
    def get(self, request):
        if settings.PROMETHEUS_EXPORTER_SECRET:
            authorization = request.headers.get("Authorization", "")
            match = RE_AUTH_TOKEN.match(authorization)
            token = match.groups()[0] if match else None
            if not token or token != settings.PROMETHEUS_EXPORTER_SECRET:
                return HttpResponse(status=401)

        result = generate_latest(application_metrics_registry).decode("utf-8")
        return HttpResponse(result, content_type="text/plain; version=0.0.4; charset=utf-8")
