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
        AlertReceiveChannel = apps.get_model("alerts", "AlertReceiveChannel")

        return (
            self.is_default
            or self.check_filter(json.dumps(raw_request_data))
            or self.check_filter(str(title))
            or
            # Special case for Amazon SNS
            (
                self.check_filter(str(message))
                if self.alert_receive_channel.integration == AlertReceiveChannel.INTEGRATION_AMAZON_SNS
                else False
            )
        )

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
    def repr_settings_for_client_side_logging(self):
        """
        Example of execution:
            term: .*, order: 0, slack notification allowed: Yes, telegram notification allowed: Yes,
            slack channel: without_amixr_general_channel, telegram channel: default
        """
        result = (
            f"term: {self.str_for_clients}, order: {self.order}, slack notification allowed: "
            f"{'Yes' if self.notify_in_slack else 'No'}, telegram notification allowed: "
            f"{'Yes' if self.notify_in_telegram else 'No'}"
        )
        if self.notification_backends:
            for backend_id, backend in self.notification_backends.items():
                result += f", {backend_id} notification allowed: {'Yes' if backend.get('enabled') else 'No'}"
        slack_channel = None
        if self.slack_channel_id:
            SlackChannel = apps.get_model("slack", "SlackChannel")
            sti = self.alert_receive_channel.organization.slack_team_identity
            slack_channel = SlackChannel.objects.filter(slack_team_identity=sti, slack_id=self.slack_channel_id).first()
        result += f", slack channel: {slack_channel.name if slack_channel else 'default'}"
        result += f", telegram channel: {self.telegram_channel.channel_name if self.telegram_channel else 'default'}"
        if self.notification_backends:
            for backend_id, backend in self.notification_backends.items():
                channel = backend.get("channel_id") or "default"
                result += f", {backend_id} channel: {channel}"
        result += f", escalation chain: {self.escalation_chain.name if self.escalation_chain else 'not selected'}"
        return result

    @property
    def str_for_clients(self):
        if self.filtering_term is None:
            return "default"
        return str(self.filtering_term).replace("`", "")

    @property
    def verbal_name_for_clients(self):
        return "default route" if self.is_default else f"route `{self.str_for_clients}`"

    def send_demo_alert(self):
        integration = self.alert_receive_channel
        integration.send_demo_alert(force_route_id=self.pk)
