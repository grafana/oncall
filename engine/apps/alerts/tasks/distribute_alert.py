from django.conf import settings

from apps.alerts.signals import alert_create_signal
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

from .task_logger import task_logger


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def send_alert_create_signal(alert_id):
    from apps.alerts.models import Alert, AlertReceiveChannel

    task_logger.debug(f"Started send_alert_create_signal task  for alert {alert_id}")
    try:
        alert = Alert.objects.get(pk=alert_id)
    except Alert.DoesNotExist:
        task_logger.info(f"Alert {alert_id} does not exist, likely parent alert group was deleted")
        return

    if alert.group.channel.maintenance_mode != AlertReceiveChannel.MAINTENANCE:
        alert_create_signal.send(
            sender=send_alert_create_signal,
            alert=alert_id,
        )
    task_logger.debug(f"Finished send_alert_create_signal task for alert {alert_id} ")
