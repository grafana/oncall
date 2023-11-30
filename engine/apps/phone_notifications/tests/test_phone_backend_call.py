from unittest import mock

import pytest
from django.test import override_settings

from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord
from apps.phone_notifications.exceptions import (
    CallsLimitExceeded,
    FailedToMakeCall,
    NumberNotVerified,
    ProviderNotSupports,
)
from apps.phone_notifications.models import PhoneCallRecord
from apps.phone_notifications.phone_backend import PhoneBackend

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


@pytest.mark.django_db
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._notify_by_provider_call")
@override_settings(GRAFANA_CLOUD_NOTIFICATIONS_ENABLED=False)
def test_notify_by_call_uses_provider(mock_notify_by_provider_call, setup):
    """
    test if make_provider_call called when GRAFANA_CLOUD_NOTIFICATIONS_ENABLED is False
    """
    user, alert_group, notification_policy = setup

    phone_backend = PhoneBackend()
    phone_backend.notify_by_call(user, alert_group, notification_policy)

    assert mock_notify_by_provider_call.called
    assert (
        PhoneCallRecord.objects.filter(
            exceeded_limit=False,
            represents_alert_group=alert_group,
            notification_policy=notification_policy,
            receiver=user,
            grafana_cloud_notification=False,
        ).count()
        == 1
    )


@pytest.mark.django_db
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._notify_by_cloud_call")
@override_settings(GRAFANA_CLOUD_NOTIFICATIONS_ENABLED=True)
def test_notify_by_call_uses_cloud(mock_notify_by_cloud_call, setup):
    """
    test if notify_by_cloud_call called when GRAFANA_CLOUD_NOTIFICATIONS_ENABLED is True
    """
    user, alert_group, notification_policy = setup

    phone_backend = PhoneBackend()
    phone_backend.notify_by_call(user, alert_group, notification_policy)

    assert mock_notify_by_cloud_call.called
    assert (
        PhoneCallRecord.objects.filter(
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
def test_notify_by_provider_call_raises_number_not_verified(
    mock_validate_user_number,
    make_organization_and_user,
):
    _, user = make_organization_and_user()
    phone_backend = PhoneBackend()

    with pytest.raises(NumberNotVerified):
        phone_backend._notify_by_provider_call(user, "some_message")


@pytest.mark.django_db
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._validate_user_number", return_value=True)
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._validate_phone_calls_left", return_value=0)
@mock.patch("apps.phone_notifications.tests.mock_phone_provider.MockPhoneProvider.make_notification_call")
@override_settings(GRAFANA_CLOUD_NOTIFICATIONS_ENABLED=False)
def test_notify_by_provider_call_rases_limit_exceeded(
    mock_make_notification_call,
    mock_phone_calls_left,
    mock_validate_user_number,
    make_organization_and_user,
):
    """
    test if CallsLimitExceeded raised when phone notifications limit is empty
    """
    _, user = make_organization_and_user()
    phone_backend = PhoneBackend()

    with pytest.raises(CallsLimitExceeded):
        phone_backend._notify_by_provider_call(user, "some_message")
    assert mock_make_notification_call.called is False
    assert PhoneCallRecord.objects.all().count() == 0


@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._validate_user_number", return_value=True)
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._validate_phone_calls_left", return_value=2)
@mock.patch(
    "apps.phone_notifications.phone_backend.PhoneBackend._add_call_limit_warning", return_value="mock warning value"
)
@mock.patch("apps.phone_notifications.tests.mock_phone_provider.MockPhoneProvider.make_notification_call")
@override_settings(GRAFANA_CLOUD_NOTIFICATIONS_ENABLED=False)
@pytest.mark.django_db
def test_notify_by_provider_call_limits_warning(
    mock_make_notification_call,
    mock_add_call_limit_warning,
    mock_validate_phone_calls_left,
    mock_validate_user_number,
    make_organization_and_user,
):
    """
    test if warning message added to call message, when almost no phone notifications left
    """
    _, user = make_organization_and_user()
    phone_backend = PhoneBackend()
    phone_backend._notify_by_provider_call(user, "some_message")

    mock_add_call_limit_warning.assert_called_once_with(2, "some_message")


@pytest.mark.django_db
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._notify_by_provider_call")
@pytest.mark.parametrize(
    "exc,log_err_code",
    [
        (NumberNotVerified, UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_NUMBER_IS_NOT_VERIFIED),
        (CallsLimitExceeded, UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_CALLS_LIMIT_EXCEEDED),
        (FailedToMakeCall, UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_NOT_ABLE_TO_CALL),
        (ProviderNotSupports, UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_NOT_ABLE_TO_CALL),
    ],
)
@override_settings(GRAFANA_CLOUD_NOTIFICATIONS_ENABLED=False)
def test_notify_by_call_handles_exceptions_from_provider(
    mock_notify_by_provider_call,
    setup,
    exc,
    log_err_code,
):
    """
    test if UserNotificationPolicyLogRecord is created when exception is raised from _notify_by_provider_call.
    _notify_by_provider_call is mocked to raise exceptions which may occur while checking if phone call possible to male and
    exceptions from phone_provider also
    """
    user, alert_group, notification_policy = setup
    mock_notify_by_provider_call.side_effect = exc

    phone_backend = PhoneBackend()
    phone_backend.notify_by_call(user, alert_group, notification_policy)

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
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._notify_by_cloud_call")
@pytest.mark.parametrize(
    "exc,log_err_code",
    [
        (FailedToMakeCall, UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_NOT_ABLE_TO_CALL),
        (NumberNotVerified, UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_NUMBER_IS_NOT_VERIFIED),
        (CallsLimitExceeded, UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_CALLS_LIMIT_EXCEEDED),
    ],
)
@override_settings(GRAFANA_CLOUD_NOTIFICATIONS_ENABLED=True)
def test_notify_by_cloud_call_handles_exceptions_from_cloud(
    mock_notify_by_cloud_call,
    setup,
    exc,
    log_err_code,
):
    """
    test if UserNotificationPolicyLogRecord is created when exception is raised from _notify_by_cloud_call
    """
    user, alert_group, notification_policy = setup
    mock_notify_by_cloud_call.side_effect = exc

    phone_backend = PhoneBackend()
    phone_backend.notify_by_call(user, alert_group, notification_policy)

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
