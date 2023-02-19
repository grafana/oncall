from django.apps import apps
from django.conf import settings

from apps.alerts.constants import TASK_DELAY_SECONDS
from apps.alerts.signals import alert_create_signal
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

from .task_logger import task_logger


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None, default_retry_delay=60
)
def distribute_alert(alert_id):
    """
    We need this task to make task processing async and to make sure the task is delivered.
    """
    Alert = apps.get_model("alerts", "Alert")
    AlertGroup = apps.get_model("alerts", "AlertGroup")
    AlertReceiveChannel = apps.get_model("alerts", "AlertReceiveChannel")

    alert = Alert.objects.get(pk=alert_id)
    alert_group = AlertGroup.all_objects.filter(pk=alert.group_id).get()
    task_logger.debug(f"Start distribute_alert for alert {alert_id} from alert_group {alert.group_id}")

    is_on_maintenace_mode = (
        alert_group.channel.maintenance_mode == AlertReceiveChannel.MAINTENANCE
        or alert_group.channel.organization.maintenance_mode == AlertReceiveChannel.MAINTENANCE
    )
    is_on_debug_mode = (
        alert_group.channel.maintenance_mode == AlertReceiveChannel.DEBUG_MAINTENANCE
        or alert_group.channel.organization.maintenance_mode == AlertReceiveChannel.DEBUG_MAINTENANCE
    )
    if not is_on_maintenace_mode:
        send_alert_create_signal.apply_async((alert_id,))
    else:
        task_logger.debug(
            f'distribute_alert: alert_id={alert_id} alert_group={alert.group_id} msg="skip create_alert_singnal due to maintenace mode"'
        )
    if not is_on_debug_mode:
        if alert.is_the_first_alert_in_group:
            # If it's the first alert, let's launch the escalation!
            alert_group.start_escalation_if_needed(countdown=TASK_DELAY_SECONDS)
    else:
        task_logger.debug(
            f'distribute_alert: alert_id={alert_id} alert_group={alert.group_id} msg="skip escalation due to debug mode"'
        )
    updated_rows = Alert.objects.filter(pk=alert_id, delivered=True).update(delivered=True)
    if updated_rows != 1:
        task_logger.critical(
            f"Tried to mark alert {alert_id} as delivered but it's already marked as delivered. Possible concurrency issue."
        )

    task_logger.debug(f"Finish distribute_alert for alert {alert_id} from alert_group {alert.group_id}")


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=0 if settings.DEBUG else None
)
def send_alert_create_signal(alert_id):
    task_logger.debug(f"Started send_alert_create_signal task  for alert {alert_id}")
    alert_create_signal.send(
        sender=send_alert_create_signal,
        alert=alert_id,
    )
    task_logger.debug(f"Finished send_alert_create_signal task for alert {alert_id} ")
