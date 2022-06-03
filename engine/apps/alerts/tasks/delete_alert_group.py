from celery.utils.log import get_task_logger
from django.apps import apps
from django.conf import settings

from common.custom_celery_tasks import shared_dedicated_queue_retry_task

logger = get_task_logger(__name__)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def delete_alert_group(alert_group_pk, user_pk):
    AlertGroup = apps.get_model("alerts", "AlertGroup")
    User = apps.get_model("user_management", "User")
    alert_group = AlertGroup.all_objects.filter(pk=alert_group_pk).first()
    if not alert_group:
        logger.debug("Alert group not found, skipping delete_alert_group")
        return

    user = User.objects.filter(pk=user_pk).first()
    if not user:
        logger.debug("User not found, skipping delete_alert_group")
        return

    alert_group.delete_by_user(user)
