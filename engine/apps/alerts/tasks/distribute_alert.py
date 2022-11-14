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

    alert = Alert.objects.get(pk=alert_id)

    task_logger.debug(f"Start distribute_alert for alert {alert_id} from alert_group {alert.group_id}")
    send_alert_create_signal.apply_async((alert_id,))

    # I don't understand what does this part
    # TODO: check it with the author
    # updated_rows = Alert.objects.filter(pk=alert_id, delivered=True).update(delivered=True)
    # if updated_rows != 1:
    #     task_logger.critical(
    #         f"Tried to mark alert {alert_id} as delivered but it's already marked as delivered. Possible concurrency issue."
    #     )

    task_logger.debug(f"Finish distribute_alert for alert {alert_id} from alert_group {alert.group_id}")


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None, default_retry_delay=60
)
def distribute_alert_group(
    alert_group_id,
):
    AlertGroup = apps.get_model("alerts", "AlertGroup")
    alert_group = AlertGroup.all_objects.get(pk=alert_group_id)

    task_logger.debug(f"Start distribute_alert_group for alert_group {alert_group_id}")
    alert_group.start_escalation_if_needed(countdown=TASK_DELAY_SECONDS)
    task_logger.debug(f"Finish distribute_alert_group for alert_group {alert_group_id}")


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
