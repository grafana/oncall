from unittest import mock

import pytest

from apps.twilioapp.phone_provider import TwilioPhoneProvider


class MockTwilioCallInstance:
    status = "mock_status"
    sid = "mock_sid"


@pytest.mark.django_db
@mock.patch("apps.twilioapp.phone_provider.TwilioPhoneProvider._call_create", return_value=MockTwilioCallInstance())
@mock.patch("apps.twilioapp.phone_provider.TwilioPhoneProvider._message_to_twiml", return_value="mocked_twiml")
def test_make_notification_call(mock_twiml, mock_call_create):
    number = "+1234567890"
    message = "Hello"
    provider = TwilioPhoneProvider()
    provider_call = provider.make_notification_call(number, message)
    mock_call_create.assert_called_once_with("mocked_twiml", number, with_callback=True)
    assert provider_call is not None
    assert provider_call.sid == MockTwilioCallInstance.sid
    assert provider_call.id is None  # test that provider_call is returned by notification call and NOT saved


@pytest.mark.django_db
@mock.patch("apps.twilioapp.phone_provider.TwilioPhoneProvider._call_create", return_value=MockTwilioCallInstance())
@mock.patch("apps.twilioapp.phone_provider.TwilioPhoneProvider._message_to_twiml", return_value="mocked_twiml")
def test_make_call(mock_twiml, mock_call_create):
    number = "+1234567890"
    message = "Hello"
    provider = TwilioPhoneProvider()
    provider_call = provider.make_call(number, message)
    assert provider_call is None  # test that provider_call is not returned from make_call
    mock_call_create.assert_called_once_with("mocked_twiml", number, with_callback=False)


class MockTwilioSMSInstance:
    status = "mock_status"
    sid = "mock_sid"


@pytest.mark.django_db
@mock.patch("apps.twilioapp.phone_provider.TwilioPhoneProvider._messages_create", return_value=MockTwilioSMSInstance())
def test_send_notification_sms(mock_messages_create):
    number = "+1234567890"
    message = "Hello"
    provider = TwilioPhoneProvider()
    provider_sms = provider.send_notification_sms(number, message)
    mock_messages_create.assert_called_once_with(number, message, with_callback=True)
    assert provider_sms is not None
    assert provider_sms.sid == MockTwilioCallInstance.sid
    assert provider_sms.id is None  # test that provider_call is returned by notification call and NOT saved


@pytest.mark.django_db
@mock.patch("apps.twilioapp.phone_provider.TwilioPhoneProvider._messages_create", return_value=MockTwilioSMSInstance())
def test_send_sms(mock_messages_create):
    number = "+1234567890"
    message = "Hello"
    provider = TwilioPhoneProvider()
    provider_sms = provider.send_sms(number, message)
    assert provider_sms is None  # test that provider_sms is not returned from send_sms
    mock_messages_create.assert_called_once_with(number, message, with_callback=False)
