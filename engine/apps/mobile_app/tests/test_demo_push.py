import pytest

from apps.mobile_app.demo_push import _get_test_escalation_fcm_message, get_test_push_title
from apps.mobile_app.models import FCMDevice, MobileAppUserSettings


@pytest.mark.django_db
def test_test_escalation_fcm_message_user_settings(
    make_organization_and_user, make_alert_receive_channel, make_alert_group, make_alert
):
    organization, user = make_organization_and_user()
    device = FCMDevice.objects.create(user=user, registration_id="test_device_id")

    message = _get_test_escalation_fcm_message(user, device, critical=False)

    # Check user settings are passed to FCM message
    assert message.data["default_notification_sound_name"] == "default_sound.mp3"
    assert message.data["default_notification_volume_type"] == "constant"
    assert message.data["default_notification_volume_override"] == "false"
    assert message.data["default_notification_volume"] == "0.8"
    assert message.data["important_notification_sound_name"] == "default_sound_important.mp3"
    assert message.data["important_notification_volume_type"] == "constant"
    assert message.data["important_notification_volume"] == "0.8"
    assert message.data["important_notification_volume_override"] == "true"
    assert message.data["important_notification_override_dnd"] == "true"

    # Check APNS notification sound is set correctly
    apns_sound = message.apns.payload.aps.sound
    assert apns_sound.critical is False
    assert apns_sound.name == "default_sound.aiff"
    assert apns_sound.volume is None  # APNS doesn't allow to specify volume for non-critical notifications

    # Check expected test push content
    assert message.apns.payload.aps.badge is None
    assert message.apns.payload.aps.alert.title == get_test_push_title(critical=False)
    assert message.data["title"] == get_test_push_title(critical=False)
    assert message.data["type"] == "oncall.message"


@pytest.mark.django_db
def test_escalation_fcm_message_user_settings_critical(
    make_organization_and_user, make_alert_receive_channel, make_alert_group, make_alert
):
    organization, user = make_organization_and_user()
    device = FCMDevice.objects.create(user=user, registration_id="test_device_id")

    message = _get_test_escalation_fcm_message(user, device, critical=True)

    # Check user settings are passed to FCM message
    assert message.data["default_notification_sound_name"] == "default_sound.mp3"
    assert message.data["default_notification_volume_type"] == "constant"
    assert message.data["default_notification_volume_override"] == "false"
    assert message.data["default_notification_volume"] == "0.8"
    assert message.data["important_notification_sound_name"] == "default_sound_important.mp3"
    assert message.data["important_notification_volume_type"] == "constant"
    assert message.data["important_notification_volume"] == "0.8"
    assert message.data["important_notification_volume_override"] == "true"
    assert message.data["important_notification_override_dnd"] == "true"

    # Check APNS notification sound is set correctly
    apns_sound = message.apns.payload.aps.sound
    assert apns_sound.critical is True
    assert apns_sound.name == "default_sound_important.aiff"
    assert apns_sound.volume == 0.8
    assert message.apns.payload.aps.custom_data["interruption-level"] == "critical"

    # Check expected test push content
    assert message.apns.payload.aps.badge is None
    assert message.apns.payload.aps.alert.title == get_test_push_title(critical=True)
    assert message.data["title"] == get_test_push_title(critical=True)
    assert message.data["type"] == "oncall.critical_message"


@pytest.mark.django_db
def test_escalation_fcm_message_user_settings_critical_override_dnd_disabled(
    make_organization_and_user, make_alert_receive_channel, make_alert_group, make_alert
):
    organization, user = make_organization_and_user()
    device = FCMDevice.objects.create(user=user, registration_id="test_device_id")

    # Disable important notification override DND
    MobileAppUserSettings.objects.create(user=user, important_notification_override_dnd=False)
    message = _get_test_escalation_fcm_message(user, device, critical=True)

    # Check user settings are passed to FCM message
    assert message.data["important_notification_override_dnd"] == "false"

    # Check APNS notification sound is set correctly
    apns_sound = message.apns.payload.aps.sound
    assert apns_sound.critical is False
    assert message.apns.payload.aps.custom_data["interruption-level"] == "time-sensitive"

    # Check expected test push content
    assert message.apns.payload.aps.badge is None
    assert message.apns.payload.aps.alert.title == get_test_push_title(critical=True)
    assert message.data["title"] == get_test_push_title(critical=True)
