from unittest import mock

import pytest
from django.test import override_settings

from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord
from apps.phone_notifications.exceptions import (
    FailedToSendSMS,
    NumberNotVerified,
    ProviderNotSupports,
    SMSLimitExceeded,
)
from apps.phone_notifications.models import SMSRecord
from apps.phone_notifications.phone_backend import PhoneBackend
from apps.phone_notifications.tests.mock_phone_provider import MockPhoneProvider

notify = UserNotificationPolicy.Step.NOTIFY
notify_by_phone = 2


@pytest.fixture()
def setup(
    make_organization_and_user, make_alert_receive_channel, make_alert_group, make_alert, make_user_notification_policy
):
    org, user = make_organization_and_user()
    arc = make_alert_receive_channel(org)
    alert_group = make_alert_group(arc)
    make_alert(alert_group, {})
    notification_policy = make_user_notification_policy(
        user, UserNotificationPolicy.Step.NOTIFY, notify_by=notify_by_phone
    )

    return user, alert_group, notification_policy


@pytest.fixture(autouse=True)
def mock_phone_provider(monkeypatch):
    def mock_get_provider(*args, **kwargs):
        return MockPhoneProvider()

    monkeypatch.setattr(PhoneBackend, "_get_phone_provider", mock_get_provider)


@pytest.mark.django_db
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._notify_by_provider_sms")
@override_settings(GRAFANA_CLOUD_NOTIFICATIONS_ENABLED=False)
def test_notify_by_sms_uses_provider(mock_notify_by_provider_sms, setup):
    """
    test if _notify_by_provider_sms called when GRAFANA_CLOUD_NOTIFICATIONS_ENABLED is False
    """
    user, alert_group, notification_policy = setup

    phone_backend = PhoneBackend()
    phone_backend.notify_by_sms(user, alert_group, notification_policy)

    assert mock_notify_by_provider_sms.called
    assert (
        SMSRecord.objects.filter(
            exceeded_limit=False,
            represents_alert_group=alert_group,
            notification_policy=notification_policy,
            receiver=user,
            grafana_cloud_notification=False,
        ).count()
        == 1
    )


@pytest.mark.django_db
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._notify_by_cloud_sms")
@override_settings(GRAFANA_CLOUD_NOTIFICATIONS_ENABLED=True)
def test_notify_by_sms_uses_cloud(mock_notify_by_cloud_sms, setup):
    """
    test if notify_by_cloud_sms called when GRAFANA_CLOUD_NOTIFICATIONS_ENABLED is True
    """
    user, alert_group, notification_policy = setup

    phone_backend = PhoneBackend()
    phone_backend.notify_by_sms(user, alert_group, notification_policy)

    assert mock_notify_by_cloud_sms.called
    assert (
        SMSRecord.objects.filter(
            exceeded_limit=False,
            represents_alert_group=alert_group,
            notification_policy=notification_policy,
            receiver=user,
            grafana_cloud_notification=False,
        ).count()
        == 1
    )


@pytest.mark.django_db
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._validate_user_number", return_value=False)
@override_settings(GRAFANA_CLOUD_NOTIFICATIONS_ENABLED=False)
def test_notify_by_provider_sms_raises_number_not_verified(
    mock_validate_user_number,
    make_organization_and_user,
):
    _, user = make_organization_and_user()
    phone_backend = PhoneBackend()

    with pytest.raises(NumberNotVerified):
        phone_backend._notify_by_provider_sms(user, "some_message")


@pytest.mark.django_db
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._validate_user_number", return_value=True)
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._validate_sms_left", return_value=0)
@mock.patch("apps.phone_notifications.tests.mock_phone_provider.MockPhoneProvider.send_notification_sms")
@override_settings(GRAFANA_CLOUD_NOTIFICATIONS_ENABLED=False)
def test_notify_by_provider_sms_raises_limit_exceeded(
    mock_send_notification_sms,
    mock_sms_left,
    mock_validate_user_number,
    make_organization_and_user,
):
    """
    test if SMSLimitExceeded raised when phone notifications limit is empty
    """
    _, user = make_organization_and_user()
    phone_backend = PhoneBackend()

    with pytest.raises(SMSLimitExceeded):
        phone_backend._notify_by_provider_sms(user, "some_message")
    assert mock_send_notification_sms.called is False
    assert SMSRecord.objects.all().count() == 0


@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._validate_user_number", return_value=True)
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._validate_sms_left", return_value=2)
@mock.patch(
    "apps.phone_notifications.phone_backend.PhoneBackend._add_sms_limit_warning", return_value="mock warning value"
)
@mock.patch("apps.phone_notifications.tests.mock_phone_provider.MockPhoneProvider.send_notification_sms")
@override_settings(GRAFANA_CLOUD_NOTIFICATIONS_ENABLED=False)
@pytest.mark.django_db
def test_notify_by_provider_sms_limits_warning(
    mock_send_notification_sms,
    mock_add_sms_limit_warning,
    mock_validate_phone_sms_left,
    mock_validate_user_number,
    make_organization_and_user,
):
    """
    test if warning message added to message, when almost no phone notifications left
    """
    _, user = make_organization_and_user()
    phone_backend = PhoneBackend()
    phone_backend._notify_by_provider_sms(user, "some_message")

    mock_add_sms_limit_warning.assert_called_once_with(2, "some_message")


@pytest.mark.django_db
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._notify_by_provider_sms")
@pytest.mark.parametrize(
    "exc,log_err_code",
    [
        (NumberNotVerified, UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_NUMBER_IS_NOT_VERIFIED),
        (SMSLimitExceeded, UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_SMS_LIMIT_EXCEEDED),
        (FailedToSendSMS, UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_NOT_ABLE_TO_SEND_SMS),
        (ProviderNotSupports, UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_NOT_ABLE_TO_SEND_SMS),
    ],
)
@override_settings(GRAFANA_CLOUD_NOTIFICATIONS_ENABLED=False)
def test_notify_by_sms_handles_exceptions_from_provider(
    mock_notify_by_provider_sms,
    setup,
    exc,
    log_err_code,
):
    """
    test if UserNotificationPolicyLogRecord is created when exception is raised from _notify_by_provider_sms.
    _notify_by_provider_sms is mocked to raise exceptions which may occur while checking if it's possible to send sms and
    exceptions from phone_provider
    """
    user, alert_group, notification_policy = setup
    mock_notify_by_provider_sms.side_effect = exc

    phone_backend = PhoneBackend()
    phone_backend.notify_by_sms(user, alert_group, notification_policy)

    assert (
        UserNotificationPolicyLogRecord.objects.filter(
            author=user,
            type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
            notification_policy=notification_policy,
            alert_group=alert_group,
            notification_error_code=log_err_code,
            notification_step=notification_policy.step,
            notification_channel=notification_policy.notify_by,
        ).count()
        == 1
    )


@pytest.mark.django_db
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._notify_by_cloud_sms")
@pytest.mark.parametrize(
    "exc,log_err_code",
    [
        (FailedToSendSMS, UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_NOT_ABLE_TO_SEND_SMS),
        (NumberNotVerified, UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_NUMBER_IS_NOT_VERIFIED),
        (SMSLimitExceeded, UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_SMS_LIMIT_EXCEEDED),
    ],
)
@override_settings(GRAFANA_CLOUD_NOTIFICATIONS_ENABLED=True)
def test_notify_by_cloud_sms_handles_exceptions_from_cloud(
    mock_notify_by_cloud_sms,
    setup,
    exc,
    log_err_code,
):
    """
    test if UserNotificationPolicyLogRecord is created when exception is raised from _notify_by_cloud_sms
    """
    user, alert_group, notification_policy = setup
    mock_notify_by_cloud_sms.side_effect = exc

    phone_backend = PhoneBackend()
    phone_backend.notify_by_sms(user, alert_group, notification_policy)

    assert (
        UserNotificationPolicyLogRecord.objects.filter(
            author=user,
            type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
            notification_policy=notification_policy,
            alert_group=alert_group,
            notification_error_code=log_err_code,
            notification_step=notification_policy.step,
            notification_channel=notification_policy.notify_by,
        ).count()
        == 1
    )
