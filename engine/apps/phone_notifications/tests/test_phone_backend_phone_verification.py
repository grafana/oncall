from unittest import mock

import pytest

from apps.phone_notifications.exceptions import NumberAlreadyVerified
from apps.phone_notifications.phone_backend import PhoneBackend
from apps.phone_notifications.tests.mock_phone_provider import MockPhoneProvider


@pytest.fixture(autouse=True)
def mock_phone_provider(monkeypatch):
    def mock_get_provider(*args, **kwargs):
        return MockPhoneProvider()

    monkeypatch.setattr(PhoneBackend, "_get_phone_provider", mock_get_provider)


@pytest.mark.django_db
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._validate_user_number", return_value=False)
@mock.patch("apps.phone_notifications.tests.mock_phone_provider.MockPhoneProvider.send_verification_sms")
def test_send_verification_sms(mock_send_verification_sms, mock_validate_user_number, make_organization_and_user):
    _, user = make_organization_and_user()
    phone_backend = PhoneBackend()

    number_to_verify = "+1234567890"
    user.unverified_phone_number = "+1234567890"
    phone_backend.send_verification_sms(user)
    mock_send_verification_sms.assert_called_once_with(number_to_verify)


@pytest.mark.django_db
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._validate_user_number", return_value=True)
@mock.patch("apps.phone_notifications.tests.mock_phone_provider.MockPhoneProvider.send_verification_sms")
def test_send_verification_sms_raises_when_number_verified(
    mock_send_verification_sms, mock__validate_user_number, make_organization_and_user
):
    _, user = make_organization_and_user()
    phone_backend = PhoneBackend()

    user.save_verified_phone_number("+1234567890")
    with pytest.raises(NumberAlreadyVerified):
        phone_backend.send_verification_sms(user)


@pytest.mark.django_db
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._validate_user_number", return_value=False)
@mock.patch("apps.phone_notifications.tests.mock_phone_provider.MockPhoneProvider.make_verification_call")
def test_make_verification_call(mock_make_verification_call, mock_validate_user_number, make_organization_and_user):
    _, user = make_organization_and_user()
    phone_backend = PhoneBackend()

    number_to_verify = "+1234567890"
    user.unverified_phone_number = "+1234567890"
    phone_backend.make_verification_call(user)
    mock_make_verification_call.assert_called_once_with(number_to_verify)


@pytest.mark.django_db
@mock.patch("apps.phone_notifications.phone_backend.PhoneBackend._validate_user_number", return_value=True)
@mock.patch("apps.phone_notifications.tests.mock_phone_provider.MockPhoneProvider.make_verification_call")
def test_make_verification_call_raises_when_number_verified(
    mock_make_verification_call, mock__validate_user_number, make_organization_and_user
):
    _, user = make_organization_and_user()
    phone_backend = PhoneBackend()

    user.save_verified_phone_number("+1234567890")
    with pytest.raises(NumberAlreadyVerified):
        phone_backend.make_verification_call(user)
