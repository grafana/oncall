import logging
import typing
from urllib.parse import urljoin

from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils import timezone

from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length

logger = logging.getLogger(__name__)


def generate_public_primary_key_for_integration_heart_beat():
    prefix = "B"
    new_public_primary_key = generate_public_primary_key(prefix)

    failure_counter = 0
    while IntegrationHeartBeat.objects.filter(public_primary_key=new_public_primary_key).exists():
        new_public_primary_key = increase_public_primary_key_length(
            failure_counter=failure_counter, prefix=prefix, model_name="IntegrationHeartBeat"
        )
        failure_counter += 1

    return new_public_primary_key


class IntegrationHeartBeat(models.Model):
    TIMEOUT_CHOICES = (
        (60, "1 minute"),
        (120, "2 minutes"),
        (180, "3 minutes"),
        (300, "5 minutes"),
        (600, "10 minutes"),
        (900, "15 minutes"),
        (1800, "30 minutes"),
        (3600, "1 hour"),
        (43200, "12 hours"),
        (86400, "1 day"),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    timeout_seconds = models.IntegerField(default=0)

    last_heartbeat_time = models.DateTimeField(default=None, null=True)
    """
    Stores the latest received heartbeat signal time
    """

    last_checkup_task_time = models.DateTimeField(default=None, null=True)
    """
    Deprecated. This field is not used. TODO: remove it
    """

    actual_check_up_task_id = models.CharField(max_length=100)
    """
    Deprecated. Stored the latest scheduled `integration_heartbeat_checkup` task id. TODO: remove it
    """

    previous_alerted_state_was_life = models.BooleanField(default=True)
    """
    Last status of the heartbeat. Determines if integration was alive on latest checkup
    """

    public_primary_key = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH + 1)],
        unique=True,
        default=generate_public_primary_key_for_integration_heart_beat,
    )

    alert_receive_channel = models.OneToOneField(
        "alerts.AlertReceiveChannel", on_delete=models.CASCADE, related_name="integration_heartbeat"
    )

    @property
    def is_expired(self) -> bool:
        if self.last_heartbeat_time is None:
            # else heartbeat flow was not received, so heartbeat can't expire.
            return False

        # if heartbeat signal was received check timeout
        return self.last_heartbeat_time + timezone.timedelta(seconds=self.timeout_seconds) < timezone.now()

    @property
    def status(self) -> bool:
        """
        Return bool indicates heartbeat status.
        True if first heartbeat signal was sent and flow is ok else False.
        If first heartbeat signal was not send it means that configuration was not finished and status not ok.
        """
        if self.last_heartbeat_time is None:
            return False
        return not self.is_expired

    @property
    def link(self) -> str:
        return urljoin(self.alert_receive_channel.integration_url, "heartbeat/")

    # Insight logs
    @property
    def insight_logs_type_verbal(self) -> str:
        return "integration_heartbeat"

    @property
    def insight_logs_verbal(self) -> str:
        return f"Integration Heartbeat for {self.alert_receive_channel.insight_logs_verbal}"

    @property
    def insight_logs_serialized(self) -> typing.Dict[str, str | int]:
        return {
            "timeout": self.timeout_seconds,
        }

    @property
    def insight_logs_metadata(self) -> typing.Dict[str, str]:
        return {
            "integration": self.alert_receive_channel.insight_logs_verbal,
            "integration_id": self.alert_receive_channel.public_primary_key,
        }
