import json
import logging

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponseBadRequest, JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django_sns_view.views import SNSEndpoint
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.alerts.models import AlertReceiveChannel, ChannelFilter, EscalationChain
from apps.auth_token.auth import IntegrationBacksyncAuthentication
from apps.heartbeat.tasks import process_heartbeat_task
from apps.integrations.legacy_prefix import has_legacy_prefix
from apps.integrations.mixins import (
    AlertChannelDefiningMixin,
    BrowsableInstructionMixin,
    IntegrationHeartBeatRateLimitMixin,
    IntegrationRateLimitMixin,
    is_ratelimit_ignored,
)
from apps.integrations.mixins.alert_forwarding_mixin import AlertForwardingMixin
from apps.integrations.tasks import create_alert, create_alertmanager_alerts
from apps.integrations.throttlers.integration_backsync_throttler import BacksyncRateThrottle
from apps.slack.models import SlackChannel
from apps.user_management.exceptions import OrganizationDeletedException, OrganizationMovedException
from apps.user_management.models import Organization, Team
from common.api_helpers.utils import create_engine_url
from settings.base import SELF_HOSTED_SETTINGS

logger = logging.getLogger(__name__)


class AmazonSNS(BrowsableInstructionMixin, AlertChannelDefiningMixin, IntegrationRateLimitMixin, SNSEndpoint):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        try:
            return super().dispatch(*args, **kwargs)
        except (OrganizationMovedException, OrganizationDeletedException, PermissionDenied) as oe:
            raise oe
        except Exception as e:
            logger.error(f"AmazonSNS - Bad Request (400) {str(e)}")
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

        timestamp = timezone.now().isoformat()
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
                "received_at": timestamp,
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
        now = timezone.now()
        for alert in request.data.get("alerts", []):
            if settings.DEBUG:
                create_alertmanager_alerts(alert_receive_channel.pk, alert, received_at=now.isoformat())
            else:
                self.execute_rate_limit_with_notification_logic()

                if self.request.limited and not is_ratelimit_ignored(alert_receive_channel):
                    return self.get_ratelimit_http_response()

                create_alertmanager_alerts.apply_async(
                    (alert_receive_channel.pk, alert), kwargs={"received_at": now.isoformat()}
                )

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

        timestamp = timezone.now().isoformat()
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
                "received_at": timestamp,
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
            AlertReceiveChannel.INTEGRATION_ADAPTIVE_GRAFANA_ALERTING,
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
            now = timezone.now()
            for alert in request.data.get("alerts", []):
                if settings.DEBUG:
                    create_alertmanager_alerts(alert_receive_channel.pk, alert, received_at=now.isoformat())
                else:
                    self.execute_rate_limit_with_notification_logic()

                    if self.request.limited and not is_ratelimit_ignored(alert_receive_channel):
                        return self.get_ratelimit_http_response()

                    create_alertmanager_alerts.apply_async(
                        (alert_receive_channel.pk, alert), kwargs={"received_at": now.isoformat()}
                    )
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

            timestamp = timezone.now().isoformat()
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
                    "received_at": timestamp,
                },
            )
        else:
            timestamp = timezone.now().isoformat()
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
                    "received_at": timestamp,
                },
            )
        return Response("Ok.")

    def check_integration_type(self, alert_receive_channel):
        return alert_receive_channel.integration == AlertReceiveChannel.INTEGRATION_GRAFANA


class UniversalAPIView(
    BrowsableInstructionMixin, AlertChannelDefiningMixin, IntegrationRateLimitMixin, APIView, AlertForwardingMixin
):
    def post(self, request, *args, **kwargs):
        if request.FILES:
            # file-objects are not serializable when queuing the task
            return HttpResponseBadRequest("File uploads are not allowed")
        alert_receive_channel = self.request.alert_receive_channel
        if not alert_receive_channel.config.slug == kwargs["integration_type"]:
            return HttpResponseBadRequest(
                f"This url is for integration with {alert_receive_channel.config.title}."
                f"Key is for {alert_receive_channel.get_integration_display()}"
            )
        if request.data is None:
            return HttpResponseBadRequest("Payload is required")

        timestamp = timezone.now().isoformat()
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
                "received_at": timestamp,
            },
        )
        return Response("Ok.")

    def dispatch(self, *args, **kwargs):
        forwarded = AlertForwardingMixin.dispatch(*args, **kwargs)
        if forwarded:
            return forwarded

        return AlertManagerAPIView.dispatch(self, *args, **kwargs)


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


class IntegrationBacksyncAPIView(APIView):
    authentication_classes = (IntegrationBacksyncAuthentication,)
    permission_classes = (IsAuthenticated,)
    throttle_classes = (BacksyncRateThrottle,)

    def post(self, request):
        alert_receive_channel = request.auth.alert_receive_channel
        integration_backsync_func = getattr(alert_receive_channel.config, "integration_backsync", None)
        if integration_backsync_func:
            integration_backsync_func(alert_receive_channel, request.data)
        return Response(status=200)


class AdaptiveGrafanaAlertingAPIView(GrafanaAlertingAPIView):
    def dispatch(self, *args, **kwargs):
        token = str(kwargs["alert_channel_key"])
        """
        TODO: Will likely need service account token + grafana url to figure out organization + author,
        Hard-coded for now
        """
        organization = None
        if settings.LICENSE != settings.OPEN_SOURCE_LICENSE_NAME:
            instance_id = self.request.headers.get("X-Grafana-Org-Id")
            if not instance_id:
                return JsonResponse({"error": "Missing header X-Grafana-Org-Id"}, status=400)
            organization = Organization.objects.filter(stack_id=instance_id).first()
        else:
            organization = Organization.objects.get(
                stack_id=SELF_HOSTED_SETTINGS["STACK_ID"], org_id=SELF_HOSTED_SETTINGS["ORG_ID"]
            )

        if not organization:
            return JsonResponse({"error": "Invalid oncall organization"}, status=400)

        routing_config, error = self.get_routing_config()
        if error:
            return JsonResponse({"error": error}, status=400)

        with transaction.atomic():
            receiver_name = routing_config.get("receiverName", None)

            team = None
            team_name = routing_config.get("teamName", None)
            if team_name:
                try:
                    team = Team.objects.get(name=team_name)
                except Team.DoesNotExist:
                    return JsonResponse({"error": "Invalid team name"}, status=400)

            alert_receive_channel, status = self.get_alert_receive_channel_from_short_term_cache(token)
            if not alert_receive_channel:
                alert_receive_channel, created = AlertReceiveChannel.objects.get_or_create(
                    verbal_name="Adaptive Grafana Alerting" if not receiver_name else receiver_name,
                    token=token,
                    organization=organization,
                    integration="adaptive_grafana_alerting",
                    team=team,
                )
                if created:
                    cache_key = AlertChannelDefiningMixin.CACHE_KEY_SHORT_TERM + "_" + token
                    cache.delete(cache_key)
            if receiver_name and receiver_name != alert_receive_channel.verbal_name:
                alert_receive_channel.verbal_name = receiver_name
                alert_receive_channel.save(update_fields=["verbal_name"])
            if team and team != alert_receive_channel.team:
                alert_receive_channel.team = team
                alert_receive_channel.save(update_fields=["team"])

            escalation_chain = None
            escalation_chain_id = routing_config.get("escalationChainId", None)
            if escalation_chain_id:
                try:
                    escalation_chain = EscalationChain.objects.get(public_primary_key=escalation_chain_id)
                except EscalationChain.DoesNotExist:
                    return JsonResponse({"error": "Invalid escalation chain"}, status=400)

            # TODO: PoC Deal with other chatops MS teams and telegram later
            slack_channel = None
            slack_channel_id = routing_config.get("chatOps", {}).get("slackChannelId", None)
            if slack_channel_id:
                try:
                    slack_channel = SlackChannel.objects.get(slack_id=slack_channel_id)
                except SlackChannel.DoesNotExist:
                    return JsonResponse({"error": "Invalid slack channel"}, status=400)

            if not escalation_chain and not slack_channel:
                return JsonResponse(
                    {"error": "At least of 1 of escalationChainId or slackChannelId must be defined"}, status=400
                )

            filtering_term = ""
            if escalation_chain_id and slack_channel:
                filtering_term = (
                    f"{{{{ payload.get('routingConfig', {{}}).get('escalationChainId', None) == '{escalation_chain_id}' "
                    "and payload.get('routingConfig', {{}}).get('chatOps', {{}}).get('slackChannelId', None) == '{slack_channel_id}' }}}}"
                )
            elif escalation_chain_id:
                filtering_term = f"{{{{ payload.get('routingConfig', {{}}).get('escalationChainId', None) == '{escalation_chain_id}' }}}}"
            elif slack_channel_id:
                filtering_term = f"{{{{ payload.get('routingConfig', {{}}).get('chatOps', {{}}).get('slackChannelId', None) == '{slack_channel_id}' }}}}"

            _, filter_created = alert_receive_channel.channel_filters.get_or_create(
                alert_receive_channel=alert_receive_channel,
                filtering_term_type=ChannelFilter.FILTERING_TERM_TYPE_JINJA2,
                escalation_chain=escalation_chain,
                slack_channel=slack_channel,
                filtering_term=filtering_term,
                notify_in_slack=slack_channel is not None,
            )

            if filter_created:
                self.update_channel_filter_order(alert_receive_channel)

        return AlertManagerAPIView.dispatch(self, *args, **kwargs)

    def get_routing_config(self):
        try:
            data = json.loads(self.request.body)
            routing_config = data.get("routingConfig", None)
            if not routing_config:
                return None, "Missing routingConfig"
            return routing_config, None
        except json.JSONDecodeError:
            return None, "Invalid JSON"

    def update_channel_filter_order(self, alert_receive_channel):
        def categorize_filtering_term(term):
            if not term:
                return 3
            return (
                0
                if "escalationChainId" in term and "slackChannelId" in term
                else 1
                if "escalationChainId" in term
                else 2
                if "slackChannelId" in term
                else 3
            )

        filters = list(alert_receive_channel.channel_filters.all().select_for_update())
        filters.sort(key=lambda obj: (categorize_filtering_term(obj.filtering_term), obj.id))
        for index, obj in enumerate(filters):
            obj.order = 1000000 + index
        ChannelFilter.objects.bulk_update(filters, ["order"])
        for index, obj in enumerate(filters):
            obj.order = index
        ChannelFilter.objects.bulk_update(filters, ["order"])
