from celery.utils.log import get_task_logger
from django.conf import settings
from push_notifications.models import APNSDevice

from apps.alerts.incident_appearance.renderers.web_renderer import AlertGroupWebRenderer
from apps.alerts.models import AlertGroup
from apps.user_management.models import User
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

MAX_RETRIES = 1 if settings.DEBUG else 10
logger = get_task_logger(__name__)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=MAX_RETRIES)
def notify_user_async(user_pk, alert_group_pk, notification_policy_pk):
    # avoid circular import
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

    devices_to_notify = APNSDevice.objects.filter(user_id=user.pk)

    # create an error log in case user has no devices set up
    if not devices_to_notify.exists():
        UserNotificationPolicyLogRecord.objects.create(
            author=user,
            type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
            notification_policy=notification_policy,
            alert_group=alert_group,
            reason="Mobile push notification error",
            notification_step=notification_policy.step,
            notification_channel=notification_policy.notify_by,
        )
        logger.error(f"Error while sending a mobile push notification: user {user_pk} has no devices set up")
        return

    # TODO: refactor this to use mobile app templates
    message = f"{AlertGroupWebRenderer(alert_group).render().get('title', 'Incident')}"
    thread_id = f"{alert_group.channel.organization.public_primary_key}:{alert_group.public_primary_key}"
    devices_to_notify.send_message(
        message,
        thread_id=thread_id,
        category="USER_NEW_INCIDENT",
        extra={
            "orgId": f"{alert_group.channel.organization.public_primary_key}",
            "orgName": f"{alert_group.channel.organization.stack_slug}",
            "incidentId": f"{alert_group.public_primary_key}",
            "status": f"{alert_group.status}",
            "aps": {
                "alert": f"{message}",
                "sound": "bingbong.aiff",
            },
        },
    )
