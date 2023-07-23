from django.conf import settings
from django.db import transaction

from common.custom_celery_tasks import shared_dedicated_queue_retry_task

from .compare_escalations import compare_escalations
from .send_alert_group_signal import send_alert_group_signal
from .task_logger import task_logger


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def unsilence_task(alert_group_pk):
    from apps.alerts.models import AlertGroup, AlertGroupLogRecord

    task_logger.info(f"Start unsilence_task for alert_group {alert_group_pk}")
    with transaction.atomic():
        try:
            alert_group = AlertGroup.objects.filter(pk=alert_group_pk).select_for_update()[0]  # Lock alert_group:
        except IndexError:
            task_logger.info(f"unsilence_task. alert_group {alert_group_pk} doesn't exist")
            return
        if not compare_escalations(unsilence_task.request.id, alert_group.unsilence_task_uuid):
            task_logger.info(
                f"unsilence_task. alert_group {alert_group.pk}.ID mismatch.Active: {alert_group.unsilence_task_uuid}"
            )
            return
        if alert_group.status == AlertGroup.SILENCED and alert_group.is_root_alert_group:
            initial_state = alert_group.state
            task_logger.info(f"unsilence alert_group {alert_group_pk} and start escalation if needed")

            alert_group.un_silence()
            # update metrics
            alert_group._update_metrics(
                organization_id=alert_group.channel.organization_id,
                previous_state=initial_state,
                state=alert_group.state,
            )
            alert_group.start_escalation_if_needed()
            un_silence_log_record = AlertGroupLogRecord(
                type=AlertGroupLogRecord.TYPE_UN_SILENCE,
                alert_group=alert_group,
                reason="auto unsilence",
            )
            un_silence_log_record.save()
            transaction.on_commit(lambda: send_alert_group_signal.apply_async((un_silence_log_record.pk,)))
        else:
            task_logger.info(
                f"Failed to unsilence alert_group {alert_group_pk}: alert_group status: {alert_group.status}, "
                f"is root: {alert_group.is_root_alert_group}"
            )
    task_logger.info(f"Finish unsilence_task for alert_group {alert_group_pk}")
