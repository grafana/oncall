import json
import logging

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import OperationalError
from django.http import HttpResponseBadRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django_sns_view.views import SNSEndpoint
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.alerts.models import AlertReceiveChannel
from apps.heartbeat.tasks import process_heartbeat_task
from apps.integrations.legacy_prefix import has_legacy_prefix
from apps.integrations.mixins import (
    AlertChannelDefiningMixin,
    BrowsableInstructionMixin,
    IntegrationHeartBeatRateLimitMixin,
    IntegrationRateLimitMixin,
    is_ratelimit_ignored,
)
from apps.integrations.tasks import create_alert, create_alertmanager_alerts
from common.api_helpers.utils import create_engine_url

logger = logging.getLogger(__name__)


class AmazonSNS(BrowsableInstructionMixin, AlertChannelDefiningMixin, IntegrationRateLimitMixin, SNSEndpoint):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        try:
            return super().dispatch(*args, **kwargs)
        except Exception as e:
            print(e)
            return JsonResponse(status=400, data={})

    def handle_message(self, message, payload):
        try:
            alert_receive_channel = self.request.alert_receive_channel
        except AlertReceiveChannel.DoesNotExist:
            raise PermissionDenied("Integration key was not found. Permission denied.")

        if type(message) is str:
            try:
                message = json.loads(message)
            except json.JSONDecodeError:
                message = message
        if type(message) is dict:
            # Here we expect CloudWatch or Beanstack payload
            message_text = "*State: {}*\n".format(message.get("NewStateValue", "NO"))
            message_text += "Region: {}\n".format(message.get("Region", "Undefined"))
            if "AlarmDescription" in message and message.get("AlarmDescription"):
                message_text += "_Description:_ {}\n".format(message.get("AlarmDescription", "Undefined"))
            message_text += message.get("NewStateReason", "")

            region = payload.get("TopicArn").split(":")[3]
            if message.get("Trigger", {}).get("Namespace") == "AWS/ElasticBeanstalk":
                link_to_upstream = "https://console.aws.amazon.com/elasticbeanstalk/home?region={}".format(region)
            else:
                link_to_upstream = "https://console.aws.amazon.com/cloudwatch//home?region={}".format(region)

            raw_request_data = message
            title = message.get("AlarmName", "Alert")
        else:
            docs_amazon_sns_url = create_engine_url("/#/integrations/amazon_sns", override_base=settings.DOCS_URL)
            title = "Alert"
            message_text = (
                "Non-JSON payload received. Please make sure you publish monitoring Alarms to SNS,"
                f" not logs: {docs_amazon_sns_url}\n" + message
            )
            link_to_upstream = None
            raw_request_data = {"message": message}

        create_alert.apply_async(
            [],
            {
                "title": title,
                "message": message_text,
                "image_url": None,
                "link_to_upstream_details": link_to_upstream,
                "alert_receive_channel_pk": alert_receive_channel.pk,
                "integration_unique_data": None,
                "raw_request_data": raw_request_data,
            },
        )


class AlertManagerAPIView(
    BrowsableInstructionMixin,
    AlertChannelDefiningMixin,
    IntegrationRateLimitMixin,
    APIView,
):
    def post(self, request):
        """
        AlertManager requires super fast response so we create Alerts in Celery Task.
        Otherwise AlertManager raises `context deadline exceeded` exception.
        Unfortunately this HTTP timeout is not configurable on AlertManager's side.
        """
        alert_receive_channel = self.request.alert_receive_channel
        if not self.check_integration_type(alert_receive_channel):
            return HttpResponseBadRequest(
                f"This url is for integration with {alert_receive_channel.get_integration_display()}. Key is for "
                + str(alert_receive_channel.get_integration_display())
            )

        if has_legacy_prefix(alert_receive_channel.integration):
            self.process_v1(request, alert_receive_channel)
        else:
            self.process_v2(request, alert_receive_channel)

        return Response("Ok.")

    def process_v1(self, request, alert_receive_channel):
        """
        process_v1 creates alerts from each alert in incoming AlertManager payload.
        """
        for alert in request.data.get("alerts", []):
            if settings.DEBUG:
                create_alertmanager_alerts(alert_receive_channel.pk, alert)
            else:
                self.execute_rate_limit_with_notification_logic()

                if self.request.limited and not is_ratelimit_ignored(alert_receive_channel):
                    return self.get_ratelimit_http_response()

                create_alertmanager_alerts.apply_async((alert_receive_channel.pk, alert))

    def process_v2(self, request, alert_receive_channel):
        """
        process_v2 creates one alert from one incoming AlertManager payload
        """
        alerts = request.data.get("alerts", [])

        data = request.data
        if "numFiring" not in request.data:
            # Count firing and resolved alerts manually if not present in payload
            num_firing = len(list(filter(lambda a: a.get("status", "") == "firing", alerts)))
            num_resolved = len(list(filter(lambda a: a.get("status", "") == "resolved", alerts)))
            data = {**request.data, "numFiring": num_firing, "numResolved": num_resolved}

        create_alert.apply_async(
            [],
            {
                "title": None,
                "message": None,
                "image_url": None,
                "link_to_upstream_details": None,
                "alert_receive_channel_pk": alert_receive_channel.pk,
                "integration_unique_data": None,
                "raw_request_data": data,
            },
        )

    def check_integration_type(self, alert_receive_channel):
        return alert_receive_channel.integration in {
            AlertReceiveChannel.INTEGRATION_ALERTMANAGER,
            AlertReceiveChannel.INTEGRATION_LEGACY_ALERTMANAGER,
        }


class GrafanaAlertingAPIView(AlertManagerAPIView):
    """Grafana Alerting has the same payload structure as AlertManager"""

    def check_integration_type(self, alert_receive_channel):
        return alert_receive_channel.integration in {
            AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING,
            AlertReceiveChannel.INTEGRATION_LEGACY_GRAFANA_ALERTING,
        }


class GrafanaAPIView(
    BrowsableInstructionMixin,
    AlertChannelDefiningMixin,
    IntegrationRateLimitMixin,
    APIView,
):
    """Support both new and old versions of Grafana Alerting"""

    def post(self, request):
        alert_receive_channel = self.request.alert_receive_channel
        if not self.check_integration_type(alert_receive_channel):
            return HttpResponseBadRequest(
                "This url is for integration with Grafana. Key is for "
                + str(alert_receive_channel.get_integration_display())
            )

        # Grafana Alerting 9 has the same payload structure as AlertManager
        if "alerts" in request.data:
            for alert in request.data.get("alerts", []):
                if settings.DEBUG:
                    create_alertmanager_alerts(alert_receive_channel.pk, alert)
                else:
                    self.execute_rate_limit_with_notification_logic()

                    if self.request.limited and not is_ratelimit_ignored(alert_receive_channel):
                        return self.get_ratelimit_http_response()

                    create_alertmanager_alerts.apply_async((alert_receive_channel.pk, alert))
            return Response("Ok.")

        """
        Example of request.data from old Grafana:
        {
            'evalMatches': [{
                'value': 100,
                'metric': 'High value',
                'tags': None
            }, {
                'value': 200,
                'metric': 'Higher Value',
                'tags': None
            }],
            'imageUrl': 'http://grafana.org/assets/img/blog/mixed_styles.png',
            'message': 'Someone is testing the alert notification within grafana.',
            'ruleId': 0,
            'ruleName': 'Test notification',
            'ruleUrl': 'http://localhost:3000/',
            'state': 'alerting',
            'title': '[Alerting] Test notification'
        }
        """
        if "attachments" in request.data:
            # Fallback in case user by mistake configured Slack url instead of webhook
            """
            {
                "parse": "full",
                "channel": "#dev",
                "attachments": [
                    {
                    "ts": 1549259302,
                    "text": " ",
                    "color": "#D63232",
                    "title": "[Alerting] Test server RAM Usage alert",
                    "fields": [
                        {
                        "short": true,
                        "title": "System",
                        "value": 1563850717.2881355
                        }
                    ],
                    "footer": "Grafana v5.4.3",
                    "fallback": "[Alerting] Test server RAM Usage alert",
                    "image_url": "",
                    "title_link": "http://abc",
                    "footer_icon": "https://grafana.com/assets/img/fav32.png"
                    }
                ]
            }
            """
            attachment = request.data["attachments"][0]

            create_alert.apply_async(
                [],
                {
                    "title": attachment.get("title", "Title"),
                    "message": "_FYI: Misconfiguration detected. Please switch integration type from Slack to WebHook in "
                    "Grafana._\n_Integration URL: {} _\n\n".format(alert_receive_channel.integration_url)
                    + attachment.get("text", ""),
                    "image_url": attachment.get("image_url", None),
                    "link_to_upstream_details": attachment.get("title_link", None),
                    "alert_receive_channel_pk": alert_receive_channel.pk,
                    "integration_unique_data": json.dumps(
                        {
                            "evalMatches": [
                                {"metric": value.get("title"), "value": str(value.get("value"))}
                                for value in attachment.get("fields", [])
                            ]
                        }
                    ),
                    "raw_request_data": request.data,
                },
            )
        else:
            create_alert.apply_async(
                [],
                {
                    "title": request.data.get("title", "Title"),
                    "message": request.data.get("message", None),
                    "image_url": request.data.get("imageUrl", None),
                    "link_to_upstream_details": request.data.get("ruleUrl", None),
                    "alert_receive_channel_pk": alert_receive_channel.pk,
                    "integration_unique_data": json.dumps({"evalMatches": request.data.get("evalMatches", [])}),
                    "raw_request_data": request.data,
                },
            )
        return Response("Ok.")

    def check_integration_type(self, alert_receive_channel):
        return alert_receive_channel.integration == AlertReceiveChannel.INTEGRATION_GRAFANA


class UniversalAPIView(BrowsableInstructionMixin, AlertChannelDefiningMixin, IntegrationRateLimitMixin, APIView):
    def post(self, request, *args, **kwargs):
        alert_receive_channel = self.request.alert_receive_channel
        if not alert_receive_channel.config.slug == kwargs["integration_type"]:
            return HttpResponseBadRequest(
                f"This url is for integration with {alert_receive_channel.config.title}."
                f"Key is for {alert_receive_channel.get_integration_display()}"
            )
        create_alert.apply_async(
            [],
            {
                "title": None,
                "message": None,
                "image_url": None,
                "link_to_upstream_details": None,
                "alert_receive_channel_pk": alert_receive_channel.pk,
                "integration_unique_data": None,
                "raw_request_data": request.data,
            },
        )
        return Response("Ok.")


class IntegrationHeartBeatAPIView(AlertChannelDefiningMixin, IntegrationHeartBeatRateLimitMixin, APIView):
    def get(self, request):
        self._process_heartbeat_signal(request, request.alert_receive_channel)
        return Response(":)")

    def post(self, request):
        self._process_heartbeat_signal(request, request.alert_receive_channel)
        return Response(status=200)

    def _process_heartbeat_signal(self, request, alert_receive_channel):
        try:
            process_heartbeat_task(alert_receive_channel.pk)
        # If database is not ready, fallback to celery task
        except OperationalError:
            process_heartbeat_task.apply_async(
                (alert_receive_channel.pk,),
            )
