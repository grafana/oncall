from celery.utils.log import get_task_logger
from django.conf import settings

from common.custom_celery_tasks import shared_dedicated_queue_retry_task
from apps.user_management.models import User
from apps.alerts.models import AlertGroup
from apps.user_webhook.alert_rendering import build_title_and_message
from apps.base.utils import live_settings
import requests

MAX_RETRIES = 1 if settings.DEBUG else 10
logger = get_task_logger(__name__)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=MAX_RETRIES)
def notify_user_async(user_pk, alert_group_pk, notification_policy_pk):
    from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord
    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        logger.warning(f"User {user_pk} does not exist")
        return

    try:
        alert_group = AlertGroup.all_objects.get(pk=alert_group_pk)
    except AlertGroup.DoesNotExist:
        logger.warning(f"Alert group {alert_group_pk} does not exist")
        return

    try:
        notification_policy = UserNotificationPolicy.objects.get(pk=notification_policy_pk)
    except UserNotificationPolicy.DoesNotExist:
        logger.warning(f"User notification policy {notification_policy_pk} does not exist")
        return

    title, message = build_title_and_message(alert_group)

    headers = {
        'Content-Type': 'application/json'
    }

    data = {
        "id": alert_group.public_primary_key,
        "title": title,
        "message": message,
        "user_email": user.email,
    }

    if live_settings.USER_WEBHOOK_TOKEN and live_settings.USER_WEBHOOK_AUTH_HEADER:
        headers[live_settings.USER_WEBHOOK_AUTH_HEADER] = live_settings.USER_WEBHOOK_TOKEN
    try:
        res = requests.post(live_settings.USER_WEBHOOK_URL, json=data, headers=headers)
        if res.status_code != 201:
            raise Exception(f"Status code was not 201. Returned status code: {res.status_code}")

    except Exception as err:
        UserNotificationPolicyLogRecord.objects.create(
            author=user,
            type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
            notification_policy=notification_policy,
            alert_group=alert_group,
            reason="Error while sending user webhook",
            notification_step=notification_policy.step,
            notification_channel=notification_policy.notify_by,
            notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_NOT_ABLE_TO_CALL
        )
        logger.error(f"Error while sending user webhook: {err}")
        return