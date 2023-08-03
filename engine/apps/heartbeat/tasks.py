from celery.utils.log import get_task_logger
from django.db import transaction
from django.db.models import DateTimeField, DurationField, ExpressionWrapper, F
from django.db.models.functions import Cast
from django.utils import timezone

from apps.heartbeat.models import IntegrationHeartBeat
from apps.integrations.tasks import create_alert
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

logger = get_task_logger(__name__)


@shared_dedicated_queue_retry_task()
def check_heartbeats() -> None:
    """
    Periodic task to check heartbeats status change and create alerts (or auto-resolve alerts) if needed
    """
    # Heartbeat is considered enabled if it
    # * has timeout_seconds set to non-zero (non-default) value,
    # * received at least one checkup (last_heartbeat_time set to non-null value)
    enabled_heartbeats = (
        IntegrationHeartBeat.objects.filter(last_heartbeat_time__isnull=False).exclude(timeout_seconds=0)
        # Convert integer `timeout_seconds`` to datetime.timedelta `timeout`
        # microseconds = seconds * 10**6
        # TODO: consider migrate timeout_seconds from IntegerField to DurationField
        .annotate(timeout=(ExpressionWrapper(F("timeout_seconds") * 10**6, output_field=DurationField())))
    )
    with transaction.atomic():
        # Heartbeat is considered expired if it
        # * is enabled,
        # * is not already expired,
        # * has not received a checkup for timeout period
        expired_heartbeats = (
            enabled_heartbeats.select_for_update()
            .filter(
                last_heartbeat_time__lte=(Cast(timezone.now(), DateTimeField()) - Cast(F("timeout"), DurationField()))
            )
            .filter(previous_alerted_state_was_life=True)
        )
        # Schedule alert creation for each expired heartbeat after transaction commit
        for heartbeat in expired_heartbeats:
            transaction.on_commit(
                lambda: create_alert.apply_async(
                    kwargs={
                        "title": heartbeat.alert_receive_channel.heartbeat_expired_title,
                        "message": heartbeat.alert_receive_channel.heartbeat_expired_message,
                        "image_url": None,
                        "link_to_upstream_details": None,
                        "alert_receive_channel_pk": heartbeat.alert_receive_channel.pk,
                        "integration_unique_data": {},
                        "raw_request_data": heartbeat.alert_receive_channel.heartbeat_expired_payload,
                    },
                )
            )
        # Update previous_alerted_state_was_life to False
        expired_count = expired_heartbeats.update(previous_alerted_state_was_life=False)
    with transaction.atomic():
        # Heartbeat is considered restored if it
        # * is enabled, expired,
        # * has received a checkup in timeout period from now,
        # * was is alerted state (previous_alerted_state_was_life is False)
        restored_heartbeats = (
            enabled_heartbeats.select_for_update()
            .filter(
                last_heartbeat_time__gte=(Cast(timezone.now(), DateTimeField()) - Cast(F("timeout"), DurationField()))
            )
            .filter(previous_alerted_state_was_life=False)
        )
        # Schedule auto-resolve alert creation for each expired heartbeat after transaction commit
        for heartbeat in restored_heartbeats:
            transaction.on_commit(
                lambda: create_alert.apply_async(
                    kwargs={
                        "title": heartbeat.alert_receive_channel.heartbeat_restored_title,
                        "message": heartbeat.alert_receive_channel.heartbeat_restored_message,
                        "image_url": None,
                        "link_to_upstream_details": None,
                        "alert_receive_channel_pk": heartbeat.alert_receive_channel.pk,
                        "integration_unique_data": {},
                        "raw_request_data": heartbeat.alert_receive_channel.heartbeat_restored_payload,
                    },
                )
            )
        restored_count = restored_heartbeats.update(previous_alerted_state_was_life=True)
    return f"Found {expired_count} expired and {restored_count} restored heartbeats"


@shared_dedicated_queue_retry_task()
def integration_heartbeat_checkup(heartbeat_id: int) -> None:
    """Deprecated. TODO: Remove this task after this task cleared from queue"""
    pass


@shared_dedicated_queue_retry_task()
def process_heartbeat_task(alert_receive_channel_pk):
    IntegrationHeartBeat.objects.filter(
        alert_receive_channel__pk=alert_receive_channel_pk,
    ).update(last_heartbeat_time=timezone.now())
