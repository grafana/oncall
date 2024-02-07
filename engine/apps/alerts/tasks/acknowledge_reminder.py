from datetime import timedelta
from functools import partial

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from common.custom_celery_tasks import shared_dedicated_queue_retry_task

from .send_alert_group_signal import send_alert_group_signal
from .task_logger import task_logger

MAX_RETRIES = 1 if settings.DEBUG else None


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=MAX_RETRIES)
def acknowledge_reminder_task(alert_group_pk: int, unacknowledge_process_id: str) -> None:
    from apps.alerts.models import AlertGroup, AlertGroupLogRecord
    from apps.user_management.models import Organization

    with transaction.atomic():
        try:
            alert_group = AlertGroup.objects.select_for_update().get(pk=alert_group_pk)  # Lock alert_group
        except AlertGroup.DoesNotExist:
            task_logger.warning(f"AlertGroup {alert_group_pk} does not exist")
            return

        if unacknowledge_process_id != alert_group.last_unique_unacknowledge_process_id:
            return

    organization = alert_group.channel.organization

    # Get timeout values
    acknowledge_reminder_timeout = Organization.ACKNOWLEDGE_REMIND_DELAY[organization.acknowledge_remind_timeout]
    unacknowledge_timeout = Organization.UNACKNOWLEDGE_TIMEOUT_DELAY[organization.unacknowledge_timeout]

    # Don't proceed if the alert group is not in a state for acknowledgement reminder
    acknowledge_reminder_required = (
        alert_group.is_root_alert_group
        and alert_group.status == AlertGroup.ACKNOWLEDGED
        and alert_group.acknowledged_by == AlertGroup.USER
        and acknowledge_reminder_timeout
    )
    is_organization_deleted = organization.deleted_at is not None
    log_info = (
        f"acknowledge_reminder_timeout option: {acknowledge_reminder_timeout},"
        f"organization ppk: {organization.public_primary_key},"
        f"organization is deleted: {is_organization_deleted}"
    )
    if not acknowledge_reminder_required or is_organization_deleted:
        task_logger.info(f"alert group {alert_group_pk} is not in a state for acknowledgement reminder. {log_info}")
        return

    task_logger.info(f"alert group {alert_group_pk} is in a state for acknowledgement reminder. {log_info}")

    # unacknowledge_timeout_task uses acknowledged_by_confirmed to check if acknowledgement reminder has been confirmed
    # by the user. Setting to None here to indicate that the user has not confirmed the acknowledgement reminder
    alert_group.acknowledged_by_confirmed = None
    alert_group.save(update_fields=["acknowledged_by_confirmed"])

    if unacknowledge_timeout:  # "unack in N minutes if no response" is enabled
        unacknowledge_timeout_task.apply_async(
            (alert_group.pk, unacknowledge_process_id), countdown=unacknowledge_timeout
        )
    else:
        if alert_group.started_at < timezone.now() - timedelta(days=settings.ACKNOWLEDGE_REMINDER_TASK_EXPIRY_DAYS):
            task_logger.info(
                f"alert group {alert_group_pk} not renewing acknowledgement reminder, started_at is too old. {log_info}"
            )
            return
        acknowledge_reminder_task.apply_async(
            (alert_group.pk, unacknowledge_process_id), countdown=acknowledge_reminder_timeout
        )

    with transaction.atomic():
        log_record = alert_group.log_records.create(
            type=AlertGroupLogRecord.TYPE_ACK_REMINDER_TRIGGERED, author=alert_group.acknowledged_by_user
        )
        task_logger.info(f"created log record {log_record.pk}, sending signal...")
        transaction.on_commit(partial(send_alert_group_signal.delay, log_record.pk))


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=MAX_RETRIES)
def unacknowledge_timeout_task(alert_group_pk: int, unacknowledge_process_id: str) -> None:
    from apps.alerts.models import AlertGroup, AlertGroupLogRecord
    from apps.user_management.models import Organization

    with transaction.atomic():
        try:
            alert_group = AlertGroup.objects.select_for_update().get(pk=alert_group_pk)  # Lock alert_group
        except AlertGroup.DoesNotExist:
            task_logger.warning(f"AlertGroup {alert_group_pk} does not exist")
            return

        if unacknowledge_process_id != alert_group.last_unique_unacknowledge_process_id:
            return

    organization = alert_group.channel.organization

    # Get timeout values
    acknowledge_reminder_timeout = Organization.ACKNOWLEDGE_REMIND_DELAY[organization.acknowledge_remind_timeout]
    unacknowledge_timeout = Organization.UNACKNOWLEDGE_TIMEOUT_DELAY[organization.unacknowledge_timeout]

    # Don't proceed if the alert group is not in a state for auto-unacknowledge
    unacknowledge_required = (
        alert_group.is_root_alert_group
        and alert_group.status == AlertGroup.ACKNOWLEDGED
        and alert_group.acknowledged_by == AlertGroup.USER
        and acknowledge_reminder_timeout
        and unacknowledge_timeout
    )
    is_organization_deleted = organization.deleted_at is not None
    log_info = (
        f"acknowledge_reminder_timeout option: {acknowledge_reminder_timeout},"
        f"unacknowledge_timeout option: {unacknowledge_timeout},"
        f"organization ppk: {organization.public_primary_key},"
        f"organization is deleted: {is_organization_deleted}"
    )
    if not unacknowledge_required or is_organization_deleted:
        task_logger.info(f"alert group {alert_group_pk} is not in a state for unacknowledge by timeout. {log_info}")
        return

    if alert_group.acknowledged_by_confirmed:  # acknowledgement reminder was confirmed by the user
        acknowledge_reminder_task.apply_async(
            (alert_group_pk, unacknowledge_process_id), countdown=acknowledge_reminder_timeout - unacknowledge_timeout
        )
        task_logger.info(
            f"Acknowledgement reminder was confirmed by user. Rescheduling acknowledge_reminder_task..."
            f"alert group: {alert_group_pk}, {log_info}"
        )
        return

    task_logger.info(f"alert group {alert_group_pk} is in a state for unacknowledge by timeout. {log_info}")
    # If acknowledgement reminder wasn't confirmed by the user, unacknowledge the alert group and start escalation again
    log_record = alert_group.log_records.create(
        type=AlertGroupLogRecord.TYPE_AUTO_UN_ACK, author=alert_group.acknowledged_by_user
    )
    transaction.on_commit(partial(send_alert_group_signal.delay, log_record.pk))
    alert_group.unacknowledge()
    alert_group.start_escalation_if_needed()
