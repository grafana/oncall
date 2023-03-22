from django.conf import settings
from django.http import Http404, HttpResponse
from prometheus_client import generate_latest
from rest_framework.views import APIView

from .metrics_exporter_manager import MetricsExporterManager


def is_internal(request):
    return request.META.get("REMOTE_ADDR") in settings.INTERNAL_IPS


class MetricsExporterView(APIView):
    def get(self, request):
        if not is_internal(request):
            raise Http404

        metrics_registry = MetricsExporterManager.collect_metrics_from_cache()  # todo:metrics: add org_id
        result = generate_latest(metrics_registry).decode("utf-8")
        return HttpResponse(result, content_type="text/plain; version=0.0.4; charset=utf-8")
