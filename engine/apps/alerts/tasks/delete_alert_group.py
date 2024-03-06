from celery.utils.log import get_task_logger
from django.conf import settings

from apps.alerts.signals import alert_group_action_triggered_signal
from apps.slack.errors import SlackAPIRatelimitError
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

logger = get_task_logger(__name__)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def delete_alert_group(alert_group_pk: int, user_pk: int) -> None:
    from apps.alerts.models import AlertGroup
    from apps.user_management.models import User

    alert_group = AlertGroup.objects.filter(pk=alert_group_pk).first()
    if not alert_group:
        logger.debug("Alert group not found, skipping delete_alert_group")
        return

    user = User.objects.filter(pk=user_pk).first()
    if not user:
        logger.debug("User not found, skipping delete_alert_group")
        return

    logger.debug(f"User {user} is deleting alert group {alert_group} (channel: {alert_group.channel})")
    alert_group.delete_by_user(user)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def send_alert_group_signal_for_delete(alert_group_pk: int, log_record_pk: int) -> None:
    try:
        alert_group_action_triggered_signal.send(
            sender=send_alert_group_signal_for_delete,
            log_record=log_record_pk,
            force_sync=True,
        )
    except SlackAPIRatelimitError as e:
        # Handle Slack API ratelimit raised in apps.slack.scenarios.distribute_alerts.DeleteGroupStep.process_signal
        send_alert_group_signal_for_delete.apply_async((alert_group_pk, log_record_pk), countdown=e.retry_after)
        return

    finish_delete_alert_group.apply_async((alert_group_pk,))


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def finish_delete_alert_group(alert_group_pk: int) -> None:
    from apps.alerts.models import AlertGroup

    alert_group = AlertGroup.objects.filter(pk=alert_group_pk).first()
    if not alert_group:
        logger.debug(f"Alert group id={alert_group_pk} not found, already deleted")
        return
    alert_group.finish_delete_by_user()
