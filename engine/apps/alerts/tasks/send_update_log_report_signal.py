from django.conf import settings

from apps.alerts.signals import alert_group_update_log_report_signal
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

from .task_logger import task_logger


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def send_update_log_report_signal(log_record_pk=None, alert_group_pk=None):
    from apps.alerts.models import AlertGroup, AlertReceiveChannel

    alert_group = AlertGroup.objects.get(id=alert_group_pk)
    if alert_group.is_maintenance_incident:
        task_logger.debug(
            f'send_update_log_report_signal: alert_group={alert_group_pk} msg="skip alert_group_update_log_report_signal, alert group is maintenance incident "'
        )
        return

    if alert_group.channel.maintenance_mode == AlertReceiveChannel.MAINTENANCE:
        task_logger.debug(
            f'send_update_log_report_signal: alert_group={alert_group_pk} msg="skip alert_group_update_log_report_signal due to maintenace"'
        )
        return

    alert_group_update_log_report_signal.send(
        sender=send_update_log_report_signal,
        alert_group=alert_group_pk,
    )
