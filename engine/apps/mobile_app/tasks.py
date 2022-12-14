from celery.utils.log import get_task_logger
from django.conf import settings
from push_notifications.models import GCMDevice

from apps.alerts.models import AlertGroup
from apps.mobile_app.alert_rendering import get_push_notification_message
from apps.user_management.models import User
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

MAX_RETRIES = 1 if settings.DEBUG else 10
logger = get_task_logger(__name__)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=MAX_RETRIES)
def notify_user_async(user_pk, alert_group_pk, notification_policy_pk, critical):
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

    gcm_devices_to_notify = GCMDevice.objects.filter(user=user)

    # create an error log in case user has no devices set up
    if not gcm_devices_to_notify.exists():
        UserNotificationPolicyLogRecord.objects.create(
            author=user,
            type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
            notification_policy=notification_policy,
            alert_group=alert_group,
            reason="Mobile push notification error",
            notification_step=notification_policy.step,
            notification_channel=notification_policy.notify_by,
        )
        logger.info(f"Error while sending a mobile push notification: user {user_pk} has no devices set up")
        return

    message = get_push_notification_message(alert_group)
    thread_id = f"{alert_group.channel.organization.public_primary_key}:{alert_group.public_primary_key}"
    alert_title = f"Critical page: {message}" if critical else message
    # TODO: this is what will be shown in the app badge (little red bubble w/ number)
    # is this the proper thing we want to show? or is there a more valuable metric to use?
    number_of_alert_groups_firing = alert_group.alerts.count()

    extra = {
        "orgId": alert_group.channel.organization.public_primary_key,
        "orgName": alert_group.channel.organization.stack_slug,
        "alertGroupId": alert_group.public_primary_key,
        "status": alert_group.status,
        "apns": {
            # for possible iOS values, see here
            # https://developer.apple.com/documentation/usernotifications/setting_up_a_remote_notification_server/generating_a_remote_notification#2943365
            "aps": {
                "badge": number_of_alert_groups_firing,
                "sound": {
                    "critical": 1 if critical else 0,
                    "name": "ambulance.aiff" if critical else "bingbong.aiff",
                    "volume": 1,
                },
                "interruption-level": "critical" if critical else "time-sensitive",
                "alert": {
                    "title": alert_title,
                    # TODO: do we want these attributes?
                    # "subtitle": "",
                    # "body": "",
                },
            },
        },
        "android": {
            # for possible Android settings, see here
            # https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages#androidconfig
            "priority": "HIGH",
            "notification": {
                "title": alert_title,
                # TODO: do we want the body attribute?
                "body": "",
                "ticker": alert_title,
                "sound": "ambulance.mp3" if critical else "bingbong.mp3",
                "click_action": "CRITICAL_NOTIFICATION" if critical else "DEFAULT",
                "visibility": "PUBLIC",
                "notification_priority": "PRIORITY_MAX" if critical else "PRIORITY_HIGH",
                "notification_count": number_of_alert_groups_firing,
                # NOTE: we'll ignore vibrate_timings for now, but we could use it to make a weird vibration
                # pattern for critical notifications
                "vibrate_timings": [],
            },
        },
    }

    logger.info(f"Sending push notification with message: {message}; thread-id: {thread_id}; extra: {extra}")

    fcm_response = gcm_devices_to_notify.send_message(
        message, thread_id=thread_id, category="USER_NEW_ALERT_GROUP", extra=extra
    )

    # NOTE: we may want to further handle the response from FCM, but for now lets simply log it out
    # https://firebase.google.com/docs/cloud-messaging/http-server-ref#interpret-downstream
    logger.info(f"FCM response was: {fcm_response}")
