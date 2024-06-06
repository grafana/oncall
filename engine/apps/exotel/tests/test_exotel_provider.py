from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings

from apps.exotel.phone_provider import ExotelPhoneProvider


@pytest.fixture
def provider():
    return ExotelPhoneProvider()


@pytest.mark.django_db
def test_make_notification_call(provider):
    number = "1234567890"
    message = "dummy message"

    provider._call_create = MagicMock(return_value=MagicMock(json=lambda: {"Call": {"Sid": "12345"}}))
    provider.make_notification_call(number, message)
    provider._call_create.assert_called_once_with(number)


@pytest.mark.django_db
def test_make_call(provider):
    number = "1234567890"
    message = "dummy message"

    provider._call_create = MagicMock(return_value=MagicMock(json=lambda: {"Call": {"Sid": "12345"}}))
    provider.make_call(number, message)
    provider._call_create.assert_called_once_with(number, False)


@pytest.mark.django_db
def test_send_verification_sms(provider):
    verification_code = "123456"
    sms_template = "Your verification code for grafana oncall is $verification_code"
    message = "Your verification code for grafana oncall is 123456"
    number = "1234567890"

    with override_settings(EXOTEL_SMS_VERIFICATION_TEMPLATE=sms_template):
        with patch("django.core.cache.cache.set"):
            provider._generate_verification_code = MagicMock(return_value=verification_code)
            provider._send_verification_code = MagicMock(
                return_value=MagicMock(json=lambda: {"SMSMessage": {"Sid": "12345"}})
            )
            provider.send_verification_sms(number)
            provider._send_verification_code.assert_called_once_with(number, message)
