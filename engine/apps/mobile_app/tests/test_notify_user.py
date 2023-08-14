from unittest.mock import patch

import pytest
from firebase_admin.exceptions import FirebaseError

from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord
from apps.mobile_app.models import FCMDevice, MobileAppUserSettings
from apps.mobile_app.tasks import _get_alert_group_escalation_fcm_message, notify_user_async
from apps.oss_installation.models import CloudConnector

MOBILE_APP_BACKEND_ID = 5
CLOUD_LICENSE_NAME = "Cloud"
OPEN_SOURCE_LICENSE_NAME = "OpenSource"


@pytest.mark.django_db
def test_notify_user_async_cloud(
    settings,
    make_organization_and_user,
    make_user_notification_policy,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_alert,
):
    # create a user and connect a mobile device
    organization, user = make_organization_and_user()
    FCMDevice.objects.create(user=user, registration_id="test_device_id")

    # set up notification policy and alert group
    notification_policy = make_user_notification_policy(
        user,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=MOBILE_APP_BACKEND_ID,
    )
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    channel_filter = make_channel_filter(alert_receive_channel)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)
    make_alert(alert_group=alert_group, raw_request_data={})

    # check FCM is contacted directly when using the cloud license
    settings.LICENSE = CLOUD_LICENSE_NAME
    settings.IS_OPEN_SOURCE = False
    with patch.object(FCMDevice, "send_message", return_value="ok") as mock:
        notify_user_async(
            user_pk=user.pk,
            alert_group_pk=alert_group.pk,
            notification_policy_pk=notification_policy.pk,
            critical=False,
        )
        mock.assert_called()


@pytest.mark.django_db
def test_notify_user_async_oss(
    settings,
    make_organization_and_user,
    make_user_notification_policy,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_alert,
):
    # create a user and connect a mobile device
    organization, user = make_organization_and_user()
    FCMDevice.objects.create(user=user, registration_id="test_device_id")

    # set up notification policy and alert group
    notification_policy = make_user_notification_policy(
        user,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=MOBILE_APP_BACKEND_ID,
    )
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    channel_filter = make_channel_filter(alert_receive_channel)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)
    make_alert(alert_group=alert_group, raw_request_data={})

    # create cloud connection
    CloudConnector.objects.create(cloud_url="test")

    # check FCM relay is contacted when using the OSS license
    settings.LICENSE = OPEN_SOURCE_LICENSE_NAME
    with patch("apps.mobile_app.tasks.send_push_notification_to_fcm_relay", return_value="ok") as mock:
        notify_user_async(
            user_pk=user.pk,
            alert_group_pk=alert_group.pk,
            notification_policy_pk=notification_policy.pk,
            critical=False,
        )
        mock.assert_called()


@pytest.mark.django_db
def test_notify_user_async_oss_no_device_connected(
    settings,
    make_organization_and_user,
    make_user_notification_policy,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_alert,
):
    # create a user without mobile device
    organization, user = make_organization_and_user()

    # set up notification policy and alert group
    notification_policy = make_user_notification_policy(
        user,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=MOBILE_APP_BACKEND_ID,
    )
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    channel_filter = make_channel_filter(alert_receive_channel)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)
    make_alert(alert_group=alert_group, raw_request_data={})

    # create cloud connection
    CloudConnector.objects.create(cloud_url="test")

    # check FCM relay is contacted when using the OSS license
    settings.LICENSE = OPEN_SOURCE_LICENSE_NAME
    with patch("apps.mobile_app.tasks.send_push_notification_to_fcm_relay", return_value="ok") as mock:
        notify_user_async(
            user_pk=user.pk,
            alert_group_pk=alert_group.pk,
            notification_policy_pk=notification_policy.pk,
            critical=False,
        )
        mock.assert_not_called()

    log_record = alert_group.personal_log_records.last()
    assert log_record.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED


@pytest.mark.django_db
def test_notify_user_async_oss_no_cloud_connection(
    settings,
    make_organization_and_user,
    make_user_notification_policy,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_alert,
):
    # create a user and connect a mobile device
    organization, user = make_organization_and_user()
    FCMDevice.objects.create(user=user, registration_id="test_device_id")

    # set up notification policy and alert group
    notification_policy = make_user_notification_policy(
        user,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=MOBILE_APP_BACKEND_ID,
    )
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    channel_filter = make_channel_filter(alert_receive_channel)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)
    make_alert(alert_group=alert_group, raw_request_data={})

    # check FCM relay is contacted when using the OSS license
    settings.LICENSE = OPEN_SOURCE_LICENSE_NAME
    with patch("apps.mobile_app.tasks.send_push_notification_to_fcm_relay", return_value="ok") as mock:
        notify_user_async(
            user_pk=user.pk,
            alert_group_pk=alert_group.pk,
            notification_policy_pk=notification_policy.pk,
            critical=False,
        )
        mock.assert_not_called()

    log_record = alert_group.personal_log_records.last()
    assert log_record.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED


@pytest.mark.django_db
def test_notify_user_retry(
    settings,
    make_organization_and_user,
    make_user_notification_policy,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_alert,
):
    organization, user = make_organization_and_user()
    FCMDevice.objects.create(user=user, registration_id="test_device_id")

    notification_policy = make_user_notification_policy(
        user,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=MOBILE_APP_BACKEND_ID,
    )
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    channel_filter = make_channel_filter(alert_receive_channel)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)
    make_alert(alert_group=alert_group, raw_request_data={})

    settings.LICENSE = CLOUD_LICENSE_NAME
    settings.IS_OPEN_SOURCE = False
    # check that FirebaseError is raised when send_message returns it so Celery task can retry
    with patch.object(
        FCMDevice, "send_message", return_value=FirebaseError(code="test_error_code", message="test_error_message")
    ):
        with pytest.raises(FirebaseError):
            notify_user_async(
                user_pk=user.pk,
                alert_group_pk=alert_group.pk,
                notification_policy_pk=notification_policy.pk,
                critical=False,
            )


@pytest.mark.django_db
def test_fcm_message_user_settings(
    make_organization_and_user, make_alert_receive_channel, make_alert_group, make_alert
):
    organization, user = make_organization_and_user()
    device = FCMDevice.objects.create(user=user, registration_id="test_device_id")

    alert_receive_channel = make_alert_receive_channel(organization=organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data={})

    message = _get_alert_group_escalation_fcm_message(alert_group, user, device, critical=False)

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
    assert message.data["type"] == "oncall.message"

    # Check APNS notification sound is set correctly
    apns_sound = message.apns.payload.aps.sound
    assert apns_sound.critical is False
    assert apns_sound.name == "default_sound.aiff"
    assert apns_sound.volume is None  # APNS doesn't allow to specify volume for non-critical notifications


@pytest.mark.django_db
def test_fcm_message_user_settings_critical(
    make_organization_and_user, make_alert_receive_channel, make_alert_group, make_alert
):
    organization, user = make_organization_and_user()
    device = FCMDevice.objects.create(user=user, registration_id="test_device_id")

    alert_receive_channel = make_alert_receive_channel(organization=organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data={})

    message = _get_alert_group_escalation_fcm_message(alert_group, user, device, critical=True)

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
    assert message.data["type"] == "oncall.critical_message"

    # Check APNS notification sound is set correctly
    apns_sound = message.apns.payload.aps.sound
    assert apns_sound.critical is True
    assert apns_sound.name == "default_sound_important.aiff"
    assert apns_sound.volume == 0.8
    assert message.apns.payload.aps.custom_data["interruption-level"] == "critical"


@pytest.mark.django_db
def test_fcm_message_user_settings_critical_override_dnd_disabled(
    make_organization_and_user, make_alert_receive_channel, make_alert_group, make_alert
):
    organization, user = make_organization_and_user()
    device = FCMDevice.objects.create(user=user, registration_id="test_device_id")

    alert_receive_channel = make_alert_receive_channel(organization=organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data={})

    # Disable important notification override DND
    MobileAppUserSettings.objects.create(user=user, important_notification_override_dnd=False)
    message = _get_alert_group_escalation_fcm_message(alert_group, user, device, critical=True)

    # Check user settings are passed to FCM message
    assert message.data["important_notification_override_dnd"] == "false"

    # Check APNS notification sound is set correctly
    apns_sound = message.apns.payload.aps.sound
    assert apns_sound.critical is False
    assert message.apns.payload.aps.custom_data["interruption-level"] == "time-sensitive"
