import json
import logging
import typing

from celery.utils.log import get_task_logger
from firebase_admin.messaging import APNSPayload, Aps, ApsAlert, CriticalSound, Message

from apps.alerts.models import AlertGroup
from apps.mobile_app.alert_rendering import get_push_notification_subtitle
from apps.mobile_app.types import FCMMessageData, MessageType, Platform
from apps.mobile_app.utils import MAX_RETRIES, construct_fcm_message, send_push_notification
from apps.user_management.models import User
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

if typing.TYPE_CHECKING:
    from apps.mobile_app.models import FCMDevice


logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


def _get_fcm_message(alert_group: AlertGroup, user: User, device_to_notify: "FCMDevice", critical: bool) -> Message:
    # avoid circular import
    from apps.mobile_app.models import MobileAppUserSettings

    thread_id = f"{alert_group.channel.organization.public_primary_key}:{alert_group.public_primary_key}"

    alert_title = "New Important Alert" if critical else "New Alert"
    alert_subtitle = get_push_notification_subtitle(alert_group)

    mobile_app_user_settings, _ = MobileAppUserSettings.objects.get_or_create(user=user)

    # critical defines the type of notification.
    # we use overrideDND to establish if the notification should sound even if DND is on
    overrideDND = critical and mobile_app_user_settings.important_notification_override_dnd

    # APNS only allows to specify volume for critical notifications
    apns_volume = mobile_app_user_settings.important_notification_volume if critical else None
    message_type = MessageType.IMPORTANT if critical else MessageType.DEFAULT
    apns_sound_name = mobile_app_user_settings.get_notification_sound_name(message_type, Platform.IOS)

    fcm_message_data: FCMMessageData = {
        "title": alert_title,
        "subtitle": alert_subtitle,
        "orgId": alert_group.channel.organization.public_primary_key,
        "orgName": alert_group.channel.organization.stack_slug,
        "alertGroupId": alert_group.public_primary_key,
        # alert_group.status is an int so it must be casted...
        "status": str(alert_group.status),
        # Pass user settings, so the Android app can use them to play the correct sound and volume
        "default_notification_sound_name": mobile_app_user_settings.get_notification_sound_name(
            MessageType.DEFAULT, Platform.ANDROID
        ),
        "default_notification_volume_type": mobile_app_user_settings.default_notification_volume_type,
        "default_notification_volume": str(mobile_app_user_settings.default_notification_volume),
        "default_notification_volume_override": json.dumps(
            mobile_app_user_settings.default_notification_volume_override
        ),
        "important_notification_sound_name": mobile_app_user_settings.get_notification_sound_name(
            MessageType.IMPORTANT, Platform.ANDROID
        ),
        "important_notification_volume_type": mobile_app_user_settings.important_notification_volume_type,
        "important_notification_volume": str(mobile_app_user_settings.important_notification_volume),
        "important_notification_volume_override": json.dumps(
            mobile_app_user_settings.important_notification_volume_override
        ),
        "important_notification_override_dnd": json.dumps(mobile_app_user_settings.important_notification_override_dnd),
    }

    number_of_alerts = alert_group.alerts.count()
    apns_payload = APNSPayload(
        aps=Aps(
            thread_id=thread_id,
            badge=number_of_alerts,
            alert=ApsAlert(title=alert_title, subtitle=alert_subtitle),
            sound=CriticalSound(
                # The notification shouldn't be critical if the user has disabled "override DND" setting
                critical=overrideDND,
                name=apns_sound_name,
                volume=apns_volume,
            ),
            custom_data={
                "interruption-level": "critical" if overrideDND else "time-sensitive",
            },
        ),
    )

    return construct_fcm_message(message_type, device_to_notify, thread_id, fcm_message_data, apns_payload)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=MAX_RETRIES)
def notify_user_async(user_pk, alert_group_pk, notification_policy_pk, critical):
    # avoid circular import
    from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord
    from apps.mobile_app.models import FCMDevice

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

    def _create_error_log_record():
        """
        Utility method to create a UserNotificationPolicyLogRecord with error
        """
        UserNotificationPolicyLogRecord.objects.create(
            author=user,
            type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
            notification_policy=notification_policy,
            alert_group=alert_group,
            reason="Mobile push notification error",
            notification_step=notification_policy.step,
            notification_channel=notification_policy.notify_by,
        )

    device_to_notify = FCMDevice.get_active_device_for_user(user)

    # create an error log in case user has no devices set up
    if not device_to_notify:
        _create_error_log_record()
        logger.error(f"Error while sending a mobile push notification: user {user_pk} has no device set up")
        return

    message = _get_fcm_message(alert_group, user, device_to_notify, critical)
    send_push_notification(device_to_notify, message, _create_error_log_record)
