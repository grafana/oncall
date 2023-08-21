from unittest import mock

import pytest

from apps.phone_notifications.exceptions import CallsLimitExceeded, NumberNotVerified, SMSLimitExceeded
from apps.phone_notifications.phone_backend import PhoneBackend
from apps.phone_notifications.tests.mock_phone_provider import MockPhoneProvider


@pytest.fixture(autouse=True)
def mock_phone_provider(monkeypatch):
    def mock_get_provider(*args, **kwargs):
        return MockPhoneProvider()

    monkeypatch.setattr(PhoneBackend, "_get_phone_provider", mock_get_provider)


@pytest.mark.django_db
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._validate_user_number", return_value=True)
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._validate_phone_calls_left", return_value=10)
@mock.patch("apps.phone_notifications.tests.mock_phone_provider.MockPhoneProvider.make_call")
def test_relay_oss_call(
    mock_make_call,
    mock_validate_user_number,
    mock_phone_calls_left,
    make_organization_and_user,
):
    _, user = make_organization_and_user()
    phone_backend = PhoneBackend()
    phone_backend.relay_oss_call(user, "relayed_call")
    mock_make_call.assert_called_once_with(user.verified_phone_number, "relayed_call")


@pytest.mark.django_db
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._validate_user_number", return_value=False)
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._validate_phone_calls_left", return_value=10)
@mock.patch("apps.phone_notifications.tests.mock_phone_provider.MockPhoneProvider.make_call")
def test_relay_oss_call_number_not_verified(
    mock_make_call,
    mock_validate_user_number,
    mock_phone_calls_left,
    make_organization_and_user,
):
    _, user = make_organization_and_user()
    phone_backend = PhoneBackend()
    with pytest.raises(NumberNotVerified):
        phone_backend.relay_oss_call(user, "relayed_call")


@pytest.mark.django_db
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._validate_user_number", return_value=True)
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._validate_phone_calls_left", return_value=0)
@mock.patch("apps.phone_notifications.tests.mock_phone_provider.MockPhoneProvider.make_call")
def test_relay_oss_call_limit_exceed(
    mock_make_call,
    mock_validate_user_number,
    mock_phone_calls_left,
    make_organization_and_user,
):
    _, user = make_organization_and_user()
    phone_backend = PhoneBackend()
    with pytest.raises(CallsLimitExceeded):
        phone_backend.relay_oss_call(user, "relayed_call")


@pytest.mark.django_db
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._validate_user_number", return_value=True)
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._validate_sms_left", return_value=10)
@mock.patch("apps.phone_notifications.tests.mock_phone_provider.MockPhoneProvider.send_sms")
def test_relay_oss_sms(
    mock_send_sms,
    mock_validate_user_number,
    mock_sms_left,
    make_organization_and_user,
):
    _, user = make_organization_and_user()
    phone_backend = PhoneBackend()
    phone_backend.relay_oss_sms(user, "relayed_sms")
    mock_send_sms.assert_called_once_with(user.verified_phone_number, "relayed_sms")


@pytest.mark.django_db
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._validate_user_number", return_value=False)
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._validate_sms_left", return_value=10)
@mock.patch("apps.phone_notifications.tests.mock_phone_provider.MockPhoneProvider.send_sms")
def test_relay_oss_sms_number_not_verified(
    mock_send_sms,
    mock_validate_user_number,
    mock_sms_left,
    make_organization_and_user,
):
    _, user = make_organization_and_user()
    phone_backend = PhoneBackend()
    with pytest.raises(NumberNotVerified):
        phone_backend.relay_oss_sms(user, "relayed_sms")


@pytest.mark.django_db
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._validate_user_number", return_value=True)
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._validate_sms_left", return_value=0)
@mock.patch("apps.phone_notifications.tests.mock_phone_provider.MockPhoneProvider.send_sms")
def test_relay_oss_sms_limit_exceed(
    mock_send_sms,
    mock_validate_user_number,
    mock_sms_left,
    make_organization_and_user,
):
    _, user = make_organization_and_user()
    phone_backend = PhoneBackend()
    with pytest.raises(SMSLimitExceeded):
        phone_backend.relay_oss_sms(user, "relayed_sms")
