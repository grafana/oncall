import json
import logging

from django.apps import apps
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.utils import IntegrityError
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.template import loader
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django_sns_view.views import SNSEndpoint
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.alerts.models import AlertReceiveChannel
from apps.heartbeat.tasks import heartbeat_checkup, process_heartbeat_task
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

        for alert in request.data.get("alerts", []):
            if settings.DEBUG:
                create_alertmanager_alerts(alert_receive_channel.pk, alert)
            else:
                self.execute_rate_limit_with_notification_logic()

                if self.request.limited and not is_ratelimit_ignored(alert_receive_channel):
                    return self.get_ratelimit_http_response()

                create_alertmanager_alerts.apply_async((alert_receive_channel.pk, alert))

        return Response("Ok.")

    def check_integration_type(self, alert_receive_channel):
        return alert_receive_channel.integration == AlertReceiveChannel.INTEGRATION_ALERTMANAGER


class GrafanaAlertingAPIView(AlertManagerAPIView):
    """Grafana Alerting has the same payload structure as AlertManager"""

    def check_integration_type(self, alert_receive_channel):
        return alert_receive_channel.integration == AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING


class GrafanaAPIView(AlertManagerAPIView):
    """Support both new and old versions of Grafana Alerting"""

    def post(self, request):
        alert_receive_channel = self.request.alert_receive_channel
        # New Grafana has the same payload structure as AlertManager
        if "alerts" in request.data:
            return super().post(request)

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
        if not self.check_integration_type(alert_receive_channel):
            return HttpResponseBadRequest(
                "This url is for integration with Grafana. Key is for "
                + str(alert_receive_channel.get_integration_display())
            )

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


# TODO: restore HeartBeatAPIView integration or clean it up as it is not used now
class HeartBeatAPIView(AlertChannelDefiningMixin, APIView):
    def get(self, request):
        template = loader.get_template("heartbeat_link.html")
        docs_url = create_engine_url("/#/integrations/heartbeat", override_base=settings.DOCS_URL)
        return HttpResponse(
            template.render(
                {
                    "docs_url": docs_url,
                }
            )
        )

    def post(self, request):
        alert_receive_channel = self.request.alert_receive_channel
        HeartBeat = apps.get_model("heartbeat", "HeartBeat")

        if request.data.get("action") == "activate":
            # timeout_seconds
            timeout_seconds = request.data.get("timeout_seconds")
            try:
                timeout_seconds = int(timeout_seconds)
            except ValueError:
                timeout_seconds = None

            if timeout_seconds is None:
                return Response(status=400, data="timeout_seconds int expected")
            # id
            _id = request.data.get("id", "default")
            # title
            title = request.data.get("title", "Title")
            # title
            link = request.data.get("link")
            # message
            message = request.data.get("message")

            heartbeat = HeartBeat(
                alert_receive_channel=alert_receive_channel,
                timeout_seconds=timeout_seconds,
                title=title,
                message=message,
                link=link,
                user_defined_id=_id,
                last_heartbeat_time=timezone.now(),
                last_checkup_task_time=timezone.now(),
                actual_check_up_task_id="none",
            )
            try:
                heartbeat.save()
                with transaction.atomic():
                    heartbeat = HeartBeat.objects.filter(pk=heartbeat.pk).select_for_update()[0]
                    task = heartbeat_checkup.apply_async(
                        (heartbeat.pk,),
                        countdown=heartbeat.timeout_seconds,
                    )
                    heartbeat.actual_check_up_task_id = task.id
                    heartbeat.save()
            except IntegrityError:
                return Response(status=400, data="id should be unique")

        elif request.data.get("action") == "deactivate":
            _id = request.data.get("id", "default")
            try:
                heartbeat = HeartBeat.objects.filter(
                    alert_receive_channel=alert_receive_channel,
                    user_defined_id=_id,
                ).get()
                heartbeat.delete()
            except HeartBeat.DoesNotExist:
                return Response(status=400, data="heartbeat not found")

        elif request.data.get("action") == "list":
            result = []
            heartbeats = HeartBeat.objects.filter(
                alert_receive_channel=alert_receive_channel,
            ).all()
            for heartbeat in heartbeats:
                result.append(
                    {
                        "created_at": heartbeat.created_at,
                        "last_heartbeat": heartbeat.last_heartbeat_time,
                        "expiration_time": heartbeat.expiration_time,
                        "is_expired": heartbeat.is_expired,
                        "id": heartbeat.user_defined_id,
                        "title": heartbeat.title,
                        "timeout_seconds": heartbeat.timeout_seconds,
                        "link": heartbeat.link,
                        "message": heartbeat.message,
                    }
                )
            return Response(result)

        elif request.data.get("action") == "heartbeat":
            _id = request.data.get("id", "default")
            with transaction.atomic():
                try:
                    heartbeat = HeartBeat.objects.filter(
                        alert_receive_channel=alert_receive_channel,
                        user_defined_id=_id,
                    ).select_for_update()[0]
                    task = heartbeat_checkup.apply_async(
                        (heartbeat.pk,),
                        countdown=heartbeat.timeout_seconds,
                    )
                    heartbeat.actual_check_up_task_id = task.id
                    heartbeat.last_heartbeat_time = timezone.now()
                    update_fields = ["actual_check_up_task_id", "last_heartbeat_time"]
                    state_changed = heartbeat.check_heartbeat_state()
                    if state_changed:
                        update_fields.append("previous_alerted_state_was_life")
                    heartbeat.save(update_fields=update_fields)
                except IndexError:
                    return Response(status=400, data="heartbeat not found")
        return Response("Ok.")


class IntegrationHeartBeatAPIView(AlertChannelDefiningMixin, IntegrationHeartBeatRateLimitMixin, APIView):
    def get(self, request):
        self._process_heartbeat_signal(request, request.alert_receive_channel)
        return Response(":)")

    def post(self, request):
        self._process_heartbeat_signal(request, request.alert_receive_channel)
        return Response(status=200)

    def _process_heartbeat_signal(self, request, alert_receive_channel):
        process_heartbeat_task.apply_async(
            (alert_receive_channel.pk,),
        )
