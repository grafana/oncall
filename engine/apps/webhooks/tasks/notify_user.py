from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from apps.alerts.models import AlertGroup
from apps.user_management.models import User
from apps.webhooks.models import Webhook
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

MAX_RETRIES = 1 if settings.DEBUG else 10
logger = get_task_logger(__name__)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=MAX_RETRIES)
def notify_user_async(user_pk, alert_group_pk, notification_policy_pk):
    # imported here to avoid circular import error
    from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord
    from apps.webhooks.tasks import execute_webhook

    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        logger.warning(f"User {user_pk} does not exist")
        return

    try:
        alert_group = AlertGroup.objects.get(pk=alert_group_pk)
    except AlertGroup.DoesNotExist:
        logger.warning(f"Alert group {alert_group_pk} does not exist")
        return

    try:
        notification_policy = UserNotificationPolicy.objects.get(pk=notification_policy_pk)
    except UserNotificationPolicy.DoesNotExist:
        logger.warning(f"User notification policy {notification_policy_pk} does not exist")
        return

    try:
        personal_webhook = user.personal_webhook
    except ObjectDoesNotExist:
        logger.warning(f"Personal webhook is not set for user {user_pk}")
        # record log notification error
        UserNotificationPolicyLogRecord.objects.create(
            author=user,
            type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
            notification_policy=notification_policy,
            alert_group=alert_group,
            notification_step=notification_policy.step,
            notification_channel=notification_policy.notify_by,
        )
        return

    # trigger webhook via task
    execute_webhook.apply_async(
        (personal_webhook.webhook.pk, alert_group.pk, user.pk, notification_policy.pk),
        kwargs={"trigger_type": Webhook.TRIGGER_PERSONAL_NOTIFICATION},
    )

    # record log notification success
    UserNotificationPolicyLogRecord.objects.create(
        author=user,
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_SUCCESS,
        notification_policy=notification_policy,
        alert_group=alert_group,
        notification_step=notification_policy.step,
        notification_channel=notification_policy.notify_by,
    )
