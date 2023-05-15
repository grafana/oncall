from fcm_django.models import FCMDevice
from firebase_admin.messaging import Message

from apps.mobile_app.tasks import (
    FCMMessageData,
    _construct_fcm_message,
    _get_apns_payload,
    _get_fcm_notification_settings,
    _send_push_notification,
)
from apps.user_management.models import User


def send_test_push(user, critical=False):
    device_to_notify = FCMDevice.objects.filter(user=user).first()
    message = _get_test_escalation_fcm_message(user, device_to_notify, critical)
    _send_push_notification(device_to_notify, message)


def _get_test_escalation_fcm_message(user: User, device_to_notify: FCMDevice, critical: bool) -> Message:
    from apps.mobile_app.models import MobileAppUserSettings

    thread_id = f"test_push"
    alert_title = "Test push"

    mobile_app_user_settings, _ = MobileAppUserSettings.objects.get_or_create(user=user)

    fcm_notification_settinds = _get_fcm_notification_settings(mobile_app_user_settings)
    fcm_message_data: FCMMessageData = {
        "title": alert_title,
        **fcm_notification_settinds,
    }

    apns_payload = _get_apns_payload(thread_id, critical, mobile_app_user_settings, title=alert_title)

    return _construct_fcm_message(device_to_notify, thread_id, fcm_message_data, apns_payload, critical)
