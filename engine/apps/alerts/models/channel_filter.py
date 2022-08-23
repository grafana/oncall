import json
import logging
import re

from django.apps import apps
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from ordered_model.models import OrderedModel

from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length

logger = logging.getLogger(__name__)


def generate_public_primary_key_for_channel_filter():
    prefix = "R"
    new_public_primary_key = generate_public_primary_key(prefix)

    failure_counter = 0
    while ChannelFilter.objects.filter(public_primary_key=new_public_primary_key).exists():
        new_public_primary_key = increase_public_primary_key_length(
            failure_counter=failure_counter, prefix=prefix, model_name="ChannelFilter"
        )
        failure_counter += 1

    return new_public_primary_key


class ChannelFilter(OrderedModel):
    """
    Actually it's a Router based on terms now. Not a Filter.
    """

    order_with_respect_to = ("alert_receive_channel", "is_default")

    public_primary_key = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH + 1)],
        unique=True,
        default=generate_public_primary_key_for_channel_filter,
    )

    alert_receive_channel = models.ForeignKey(
        "alerts.AlertReceiveChannel", on_delete=models.CASCADE, related_name="channel_filters"
    )

    escalation_chain = models.ForeignKey(
        "alerts.EscalationChain", null=True, default=None, on_delete=models.SET_NULL, related_name="channel_filters"
    )

    notify_in_slack = models.BooleanField(null=True, default=True)
    notify_in_telegram = models.BooleanField(null=True, default=False)

    slack_channel_id = models.CharField(max_length=100, null=True, default=None)

    telegram_channel = models.ForeignKey(
        "telegram.TelegramToOrganizationConnector",
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        related_name="channel_filter",
    )

    # track additional messaging backends config
    # e.g. {'<BACKEND-ID>': {'channel': '<channel-public-key>', 'enabled': True}}
    notification_backends = models.JSONField(null=True, default=None)

    created_at = models.DateTimeField(auto_now_add=True)
    filtering_term = models.CharField(max_length=1024, null=True, default=None)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = (
            "alert_receive_channel",
            "is_default",
            "order",
        )

    def __str__(self):
        return f"{self.pk}: {self.filtering_term or 'default'}"

    @classmethod
    def select_filter(cls, alert_receive_channel, raw_request_data, title, message=None, force_route_id=None):
        # Try to find force route first if force_route_id is given
        if force_route_id is not None:
            logger.info(
                f"start select_filter with force_route_id={force_route_id} alert_receive_channel={alert_receive_channel.pk}."
            )
            try:
                satisfied_filter = cls.objects.get(
                    alert_receive_channel=alert_receive_channel.pk,
                    pk=force_route_id,
                )
                logger.info(
                    f"success select_filter with force_route_id={force_route_id} alert_receive_channel={alert_receive_channel.pk}."
                )
                return satisfied_filter
            except cls.DoesNotExist:
                # If force route was not found fallback to default routing.
                logger.info(
                    f"select_filter unable to find force_route_id={force_route_id} alert_receive_channel={alert_receive_channel.pk}."
                )
                pass

        filters = cls.objects.filter(alert_receive_channel=alert_receive_channel)

        satisfied_filter = None
        for _filter in filters:
            if satisfied_filter is None and _filter.is_satisfying(raw_request_data, title, message):
                satisfied_filter = _filter

        return satisfied_filter

    def is_satisfying(self, raw_request_data, title, message=None):
        return self.is_default or self.check_filter(json.dumps(raw_request_data)) or self.check_filter(str(title))

    def check_filter(self, value):
        return re.search(self.filtering_term, value)

    @property
    def slack_channel_id_or_general_log_id(self):
        organization = self.alert_receive_channel.organization
        slack_team_identity = organization.slack_team_identity
        if slack_team_identity is None:
            return None
        if self.slack_channel_id is None:
            return organization.general_log_channel_id
        else:
            return self.slack_channel_id

    @property
    def str_for_clients(self):
        if self.filtering_term is None:
            return "default"
        return str(self.filtering_term).replace("`", "")

    def send_demo_alert(self):
        integration = self.alert_receive_channel
        integration.send_demo_alert(force_route_id=self.pk)

    # Insight logs
    @property
    def insight_logs_type_verbal(self):
        return "route"

    @property
    def insight_logs_verbal(self):
        return f"{self.str_for_clients} for {self.alert_receive_channel.insight_logs_verbal}"

    @property
    def insight_logs_serialized(self):
        result = {
            "filtering_term": self.str_for_clients,
            "order": self.order,
            "slack_notification_enabled": self.notify_in_slack,
            "telegram_notification_enabled": self.notify_in_telegram,
            # TODO: use names instead of pks, it's needed to rework messaging backends for that
        }
        # TODO: use names instead of pks, it's needed to rework messaging backends for that
        if self.slack_channel_id:
            if self.slack_channel_id:
                SlackChannel = apps.get_model("slack", "SlackChannel")
                sti = self.alert_receive_channel.organization.slack_team_identity
                slack_channel = SlackChannel.objects.filter(
                    slack_team_identity=sti, slack_id=self.slack_channel_id
                ).first()
                result["slack_channel"] = slack_channel.name
        if self.telegram_channel:
            result["telegram_channel"] = self.telegram_channel.public_primary_key
        if self.escalation_chain:
            result["escalation_chain"] = self.escalation_chain.insight_logs_verbal
            result["escalation_chain_id"] = self.escalation_chain.public_primary_key
        if self.notification_backends:
            for backend_id, backend in self.notification_backends.items():
                channel = backend.get("channel_id") or "default"
                result[backend_id] = channel
        return result

    @property
    def insight_logs_metadata(self):
        return {
            "integration": self.alert_receive_channel.insight_logs_verbal,
            "integration_id": self.alert_receive_channel.public_primary_key,
        }
