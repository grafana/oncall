from django.apps import apps
from django.conf import settings

from apps.alerts.signals import alert_group_update_log_report_signal
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

from .task_logger import task_logger


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def send_update_log_report_signal(log_record_pk=None, alert_group_pk=None):
    AlertGroup = apps.get_model("alerts", "AlertGroup")

    if alert_group_pk is not None:
        alert_group = AlertGroup.all_objects.get(id=alert_group_pk)
        if alert_group.is_maintenance_incident:
            task_logger.debug(
                f'send_update_log_report_signal: alert_group={alert_group_pk} msg="skip alert_group_update_log_report_signal, alert group is maintenance incident "'
            )
            return

        is_on_maintenace_or_debug_mode = (
            alert_group.channel.maintenance_mode is not None
            or alert_group.channel.organization.maintenance_mode is not None
        )
        if is_on_maintenace_or_debug_mode:
            task_logger.debug(
                f'send_update_log_report_signal: alert_group={alert_group_pk} msg="skip alert_group_update_log_report_signal due to maintenace"'
            )
            return

        alert_group_update_log_report_signal.send(
            sender=send_update_log_report_signal,
            alert_group=alert_group_pk,
        )
