from django.conf import settings
from django.db import transaction

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

        if alert_group.last_unique_unacknowledge_process_id != unacknowledge_process_id:
            return

    acknowledge_reminder_timeout = Organization.ACKNOWLEDGE_REMIND_DELAY[
        alert_group.channel.organization.acknowledge_remind_timeout
    ]
    unacknowledge_timeout = Organization.UNACKNOWLEDGE_TIMEOUT_DELAY[
        alert_group.channel.organization.unacknowledge_timeout
    ]

    acknowledge_reminder_required = (
        alert_group.is_root_alert_group
        and alert_group.status == AlertGroup.ACKNOWLEDGED
        and alert_group.acknowledged_by == AlertGroup.USER
        and acknowledge_reminder_timeout
    )
    if not acknowledge_reminder_required:
        task_logger.info("AlertGroup is not in a state for acknowledge reminder")
        return

    alert_group.acknowledged_by_confirmed = None
    alert_group.save(update_fields=["acknowledged_by_confirmed"])

    if unacknowledge_timeout:
        unacknowledge_timeout_task.apply_async(
            (alert_group.pk, unacknowledge_process_id), countdown=unacknowledge_timeout
        )
    else:
        acknowledge_reminder_task.apply_async(
            (alert_group.pk, unacknowledge_process_id), countdown=acknowledge_reminder_timeout
        )

    log_record = alert_group.log_records.create(
        type=AlertGroupLogRecord.TYPE_ACK_REMINDER_TRIGGERED, author=alert_group.acknowledged_by_user
    )
    transaction.on_commit(lambda: send_alert_group_signal.delay(log_record.pk))


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=MAX_RETRIES)
def unacknowledge_timeout_task(alert_group_pk, unacknowledge_process_id):
    from apps.alerts.models import AlertGroup, AlertGroupLogRecord
    from apps.user_management.models import Organization

    log_record = None

    task_logger.info(
        f"Starting an unacknowledge task " f"for acknowledgement timeout with process id {unacknowledge_process_id}"
    )
    with transaction.atomic():
        try:
            alert_group = AlertGroup.objects.filter(pk=alert_group_pk).select_for_update()[0]  # Lock alert_group:
        except IndexError:
            return f"unacknowledge_timeout_task: Alert group with pk {alert_group_pk} doesn't exist"

        if unacknowledge_process_id == alert_group.last_unique_unacknowledge_process_id:
            if not alert_group.resolved and alert_group.acknowledged and alert_group.is_root_alert_group:
                if not alert_group.acknowledged_by_confirmed:
                    log_record = AlertGroupLogRecord(
                        type=AlertGroupLogRecord.TYPE_AUTO_UN_ACK,
                        author=alert_group.acknowledged_by_user,
                        alert_group=alert_group,
                    )
                    alert_group.unacknowledge()
                    alert_group.start_escalation_if_needed()
                else:
                    seconds_remind = Organization.ACKNOWLEDGE_REMIND_DELAY[
                        alert_group.channel.organization.acknowledge_remind_timeout
                    ]
                    seconds_unack = Organization.UNACKNOWLEDGE_TIMEOUT_DELAY[
                        alert_group.channel.organization.unacknowledge_timeout
                    ]
                    seconds = seconds_remind - seconds_unack
                    acknowledge_reminder_task.apply_async(
                        (
                            alert_group_pk,
                            unacknowledge_process_id,
                        ),
                        countdown=seconds,
                    )

    if log_record is not None:
        log_record.save()
        task_logger.debug(
            f"call send_alert_group_signal for alert_group {alert_group_pk}, "
            f"log record {log_record.pk} with type '{log_record.get_type_display()}'"
        )
        transaction.on_commit(lambda: send_alert_group_signal.apply_async((log_record.pk,)))

    task_logger.info(
        f"Starting an unacknowledge task for acknowledgement timeout with process id {unacknowledge_process_id}"
    )
