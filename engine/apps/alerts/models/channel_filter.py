import json
import logging
import re
import typing

from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models

from common.jinja_templater import apply_jinja_template
from common.jinja_templater.apply_jinja_template import JinjaTemplateError, JinjaTemplateWarning
from common.ordered_model.ordered_model import OrderedModel
from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length

if typing.TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

    from apps.alerts.models import AlertGroup

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

    alert_groups: "RelatedManager['AlertGroup']"

    order_with_respect_to = ["alert_receive_channel_id", "is_default"]

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

    FILTERING_TERM_TYPE_REGEX = 0
    FILTERING_TERM_TYPE_JINJA2 = 1
    FILTERING_TERM_TYPE_CHOICES = [
        (FILTERING_TERM_TYPE_REGEX, "regex"),
        (FILTERING_TERM_TYPE_JINJA2, "jinja2"),
    ]
    filtering_term_type = models.IntegerField(choices=FILTERING_TERM_TYPE_CHOICES, default=FILTERING_TERM_TYPE_REGEX)

    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["alert_receive_channel_id", "is_default", "order"]
        constraints = [
            models.UniqueConstraint(
                fields=["alert_receive_channel_id", "is_default", "order"], name="unique_channel_filter_order"
            )
        ]

    def __str__(self):
        return f"{self.pk}: {self.filtering_term or 'default'}"

    @classmethod
    def select_filter(cls, alert_receive_channel, raw_request_data, force_route_id=None):
        # Try to find force route first if force_route_id is given
        # Force route was used to send demo alerts to specific route.
        # It is deprecated and may be used by older versions of the plugins
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
            if satisfied_filter is None and _filter.is_satisfying(raw_request_data):
                satisfied_filter = _filter

        return satisfied_filter

    def is_satisfying(self, raw_request_data):
        return self.is_default or self.check_filter(raw_request_data)

    def check_filter(self, value):
        if self.filtering_term_type == ChannelFilter.FILTERING_TERM_TYPE_JINJA2:
            try:
                is_matching = apply_jinja_template(self.filtering_term, payload=value)
                return is_matching.strip().lower() in ["1", "true", "ok"]
            except (JinjaTemplateError, JinjaTemplateWarning):
                logger.error(f"channel_filter={self.id} failed to parse jinja2={self.filtering_term}")
                return False
        if self.filtering_term is not None and self.filtering_term_type == ChannelFilter.FILTERING_TERM_TYPE_REGEX:
            try:
                return re.search(self.filtering_term, json.dumps(value))
            except re.error:
                logger.error(f"channel_filter={self.id} failed to parse regex={self.filtering_term}")
                return False
        return False

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
        if self.is_default:
            return "default"
        if self.filtering_term_type == ChannelFilter.FILTERING_TERM_TYPE_JINJA2:
            return str(self.filtering_term)
        elif self.filtering_term_type == ChannelFilter.FILTERING_TERM_TYPE_REGEX or self.filtering_term_type is None:
            return str(self.filtering_term).replace("`", "")
        raise Exception("Unknown filtering term")

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
            "filtering_term_type": self.get_filtering_term_type_display(),
            "filtering_term": self.str_for_clients,
            "order": self.order,
            "slack_notification_enabled": self.notify_in_slack,
            "telegram_notification_enabled": self.notify_in_telegram,
        }
        if self.slack_channel_id:
            if self.slack_channel_id:
                from apps.slack.models import SlackChannel

                sti = self.alert_receive_channel.organization.slack_team_identity
                slack_channel = SlackChannel.objects.filter(
                    slack_team_identity=sti, slack_id=self.slack_channel_id
                ).first()
                if slack_channel is not None:
                    # Case when slack channel was deleted, but channel filter still has it's id
                    result["slack_channel"] = slack_channel.name
        # TODO: use names instead of pks for telegram and other notifications backends.
        # It's needed to rework messaging backends for that
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
