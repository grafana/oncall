import logging
import typing
from urllib.parse import urljoin

from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models, transaction
from django.utils import timezone

from apps.integrations.tasks import create_alert
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
    last_checkup_task_time = models.DateTimeField(default=None, null=True)
    actual_check_up_task_id = models.CharField(max_length=100)
    previous_alerted_state_was_life = models.BooleanField(default=True)

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

    @classmethod
    def perform_heartbeat_check(cls, heartbeat_id: int, task_request_id: str) -> None:
        with transaction.atomic():
            heartbeats = cls.objects.filter(pk=heartbeat_id).select_for_update()
            if len(heartbeats) == 0:
                logger.info(f"Heartbeat {heartbeat_id} not found {task_request_id}")
                return
            heartbeat = heartbeats[0]
            if task_request_id == heartbeat.actual_check_up_task_id:
                heartbeat.check_heartbeat_state_and_save()
            else:
                logger.info(f"Heartbeat {heartbeat_id} is not actual {task_request_id}")

    def check_heartbeat_state_and_save(self) -> bool:
        """
        Use this method if you want just check heartbeat status.
        """
        state_changed = self.check_heartbeat_state()
        if state_changed:
            self.save(update_fields=["previous_alerted_state_was_life"])
        return state_changed

    def check_heartbeat_state(self) -> bool:
        """
        Actually checking heartbeat.
        Use this method if you want to do changes of heartbeat instance while checking its status.
        ( See IntegrationHeartBeatAPIView.post() for example )
        """
        state_changed = False
        if self.is_expired:
            if self.previous_alerted_state_was_life:
                self.on_heartbeat_expired()
                self.previous_alerted_state_was_life = False
                state_changed = True
        else:
            if not self.previous_alerted_state_was_life:
                self.on_heartbeat_restored()
                self.previous_alerted_state_was_life = True
                state_changed = True
        return state_changed

    def on_heartbeat_restored(self) -> None:
        create_alert.apply_async(
            kwargs={
                "title": self.alert_receive_channel.heartbeat_restored_title,
                "message": self.alert_receive_channel.heartbeat_restored_message,
                "image_url": None,
                "link_to_upstream_details": None,
                "alert_receive_channel_pk": self.alert_receive_channel.pk,
                "integration_unique_data": {},
                "raw_request_data": self.alert_receive_channel.heartbeat_restored_payload,
            },
        )

    def on_heartbeat_expired(self) -> None:
        create_alert.apply_async(
            kwargs={
                "title": self.alert_receive_channel.heartbeat_expired_title,
                "message": self.alert_receive_channel.heartbeat_expired_message,
                "image_url": None,
                "link_to_upstream_details": None,
                "alert_receive_channel_pk": self.alert_receive_channel.pk,
                "integration_unique_data": {},
                "raw_request_data": self.alert_receive_channel.heartbeat_expired_payload,
            },
        )

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
