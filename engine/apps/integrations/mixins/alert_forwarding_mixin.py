import json
import logging

from django.http import JsonResponse

from apps.alerts.models import AlertReceiveChannel
from apps.grafana_plugin.helpers import GrafanaAPIClient

logger = logging.getLogger(__name__)


class AlertForwardingMixin:
    def dispatch(self, *args, **kwargs):
        if kwargs.get("integration_type") == "elastalert":
            token = str(kwargs["alert_channel_key"])
            # TODO: replace with proper caching logic later
            alert_receive_channel = AlertReceiveChannel.objects.get(token=token)
            organization = alert_receive_channel.organization
            if not alert_receive_channel:
                return JsonResponse({"error": "Invalid alert receive channel"}, status=400)

            forwarded_payload = {}
            try:
                data = json.loads(self.body)
                # Transform Here

            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON"}, status=400)

            # Forward
            client = GrafanaAPIClient(api_url=organization.grafana_url, api_token=organization.api_token)
            _, status = client.forward_alert(forwarded_payload)
            if status["status_code"] != 200:
                return JsonResponse({"status": status}, status=status["status_code"])
            return JsonResponse({"data": data}, status=200)

        return None
