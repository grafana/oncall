import time

from django.conf import settings

from apps.alerts.signals import alert_group_action_triggered_signal
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

from .task_logger import task_logger


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=0 if settings.DEBUG else None
)
def send_alert_group_signal(log_record_id):
    start_time = time.time()
    task_logger.info(f"sending signal for log record {log_record_id}")
    alert_group_action_triggered_signal.send(sender=send_alert_group_signal, log_record=log_record_id)

    print("--- %s seconds ---" % (time.time() - start_time))
