from django.conf import settings

from apps.alerts.constants import TASK_DELAY_SECONDS
from apps.alerts.signals import alert_create_signal, alert_group_escalation_snapshot_built
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

from .task_logger import task_logger


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None, default_retry_delay=60
)
def distribute_alert(alert_id):
    """
    We need this task to make task processing async and to make sure the task is delivered.
    """
    from apps.alerts.models import Alert

    alert = Alert.objects.get(pk=alert_id)
    task_logger.debug(f"Start distribute_alert for alert {alert_id} from alert_group {alert.group_id}")

    send_alert_create_signal.apply_async((alert_id,))

    # Launch escalation for the group if it's the first alert, or if the group is paused.
    # "paused" means that the current escalation step is "Continue escalation if >X alerts per Y minutes" and there are
    # not enough alerts to trigger the escalation further. Launching escalation for a paused group will re-evaluate
    # the threshold and advance the escalation if needed, or go back to the same "paused" state if the threshold is
    # still not reached.
    if alert.is_the_first_alert_in_group or alert.group.pause_escalation:
        alert.group.start_escalation_if_needed(countdown=TASK_DELAY_SECONDS)

    if alert.is_the_first_alert_in_group:
        alert_group_escalation_snapshot_built.send(sender=distribute_alert, alert_group=alert.group)

    updated_rows = Alert.objects.filter(pk=alert_id, delivered=True).update(delivered=True)
    if updated_rows != 1:
        task_logger.critical(
            f"Tried to mark alert {alert_id} as delivered but it's already marked as delivered. Possible concurrency issue."
        )

    task_logger.debug(f"Finish distribute_alert for alert {alert_id} from alert_group {alert.group_id}")


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def send_alert_create_signal(alert_id):
    from apps.alerts.models import Alert, AlertReceiveChannel

    task_logger.debug(f"Started send_alert_create_signal task  for alert {alert_id}")
    alert = Alert.objects.get(pk=alert_id)

    if alert.group.channel.maintenance_mode != AlertReceiveChannel.MAINTENANCE:
        alert_create_signal.send(
            sender=send_alert_create_signal,
            alert=alert_id,
        )
    task_logger.debug(f"Finished send_alert_create_signal task for alert {alert_id} ")
