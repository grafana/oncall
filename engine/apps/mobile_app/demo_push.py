import json
import random
import string
import typing

from firebase_admin.messaging import APNSPayload, Aps, ApsAlert, CriticalSound, Message

from apps.mobile_app.exceptions import DeviceNotSet
from apps.mobile_app.tasks import _construct_fcm_message, _send_push_notification, logger
from apps.mobile_app.types import FCMMessageData, MessageType, Platform
from apps.user_management.models import User

if typing.TYPE_CHECKING:
    from apps.mobile_app.models import FCMDevice


def send_test_push(user, critical=False):
    from apps.mobile_app.models import FCMDevice

    device_to_notify = FCMDevice.get_active_device_for_user(user)
    if device_to_notify is None:
        logger.info(f"send_test_push: fcm_device not found user_id={user.id}")
        raise DeviceNotSet
    message = _get_test_escalation_fcm_message(user, device_to_notify, critical)
    _send_push_notification(device_to_notify, message)


def _get_test_escalation_fcm_message(user: User, device_to_notify: "FCMDevice", critical: bool) -> Message:
    # TODO: this method is copied from _get_alert_group_escalation_fcm_message
    # to have same notification/sound/overrideDND logic. Ideally this logic should be abstracted, not repeated.
    from apps.mobile_app.models import MobileAppUserSettings

    thread_id = f"{''.join(random.choices(string.digits, k=6))}:test_push"

    mobile_app_user_settings, _ = MobileAppUserSettings.objects.get_or_create(user=user)
    # critical defines the type of notification.
    # we use overrideDND to establish if the notification should sound even if DND is on
    overrideDND = critical and mobile_app_user_settings.important_notification_override_dnd

    # APNS only allows to specify volume for critical notifications
    apns_volume = mobile_app_user_settings.important_notification_volume if critical else None
    message_type = MessageType.IMPORTANT if critical else MessageType.DEFAULT
    apns_sound_name = mobile_app_user_settings.get_notification_sound_name(message_type, Platform.IOS)

    fcm_message_data: FCMMessageData = {
        "title": get_test_push_title(critical),
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

    apns_payload = APNSPayload(
        aps=Aps(
            thread_id=thread_id,
            alert=ApsAlert(title=get_test_push_title(critical)),
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

    return _construct_fcm_message(message_type, device_to_notify, thread_id, fcm_message_data, apns_payload)


def get_test_push_title(critical: bool) -> str:
    return f"Hi, this is a {'critical ' if critical else ''}test notification from Grafana OnCall"
