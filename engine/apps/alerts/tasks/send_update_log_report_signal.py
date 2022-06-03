from django.apps import apps
from django.conf import settings

from apps.alerts.signals import alert_group_update_log_report_signal
from common.custom_celery_tasks import shared_dedicated_queue_retry_task


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def send_update_log_report_signal(log_record_pk=None, alert_group_pk=None):
    AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")

    if log_record_pk and not alert_group_pk:  # legacy
        log_record = AlertGroupLogRecord.objects.get(pk=log_record_pk)
        if log_record.type == AlertGroupLogRecord.TYPE_DELETED:
            return
        alert_group_pk = log_record.alert_group.pk

    if alert_group_pk is not None:
        alert_group_update_log_report_signal.send(
            sender=send_update_log_report_signal,
            alert_group=alert_group_pk,
        )
