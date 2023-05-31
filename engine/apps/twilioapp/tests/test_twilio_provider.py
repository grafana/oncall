from unittest import mock

import pytest
from twilio.base.exceptions import TwilioRestException as BaseTwilioRestException

from apps.phone_notifications.exceptions import CallOrSMSNotAllowed, FailedToMakeCall, FailedToStartVerification
from apps.twilioapp.phone_provider import TwilioPhoneProvider


class MockTwilioCallInstance:
    status = "mock_status"
    sid = "mock_sid"


class TwilioRestException(BaseTwilioRestException):
    def __init__(self, code):
        super().__init__(status=403, uri="http://example.com", msg="asdf", code=code, method="GET")


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


@pytest.mark.django_db
@pytest.mark.parametrize(
    "twilio_code,expected_exception",
    [
        (21215, CallOrSMSNotAllowed),
        (None, FailedToMakeCall),
    ],
)
@mock.patch("apps.twilioapp.phone_provider.TwilioPhoneProvider._call_create", return_value=MockTwilioCallInstance())
@mock.patch("apps.twilioapp.phone_provider.TwilioPhoneProvider._message_to_twiml", return_value="mocked_twiml")
def test_make_call_exceptions(mock_twiml, mock_call_create, twilio_code, expected_exception):
    number = "+1234567890"
    message = "Hello"
    provider = TwilioPhoneProvider()

    mock_call_create.side_effect = TwilioRestException(twilio_code)

    with pytest.raises(expected_exception):
        provider.make_call(number, message)

    mock_call_create.assert_called_once_with("mocked_twiml", number, with_callback=False)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "twilio_code,expected_exception",
    [
        (60410, CallOrSMSNotAllowed),
        (None, FailedToStartVerification),
    ],
)
@mock.patch("apps.twilioapp.phone_provider.TwilioPhoneProvider._verify_sender", return_value=MockTwilioCallInstance())
def test_send_verification_sms_exceptions(mock_verify_sender, twilio_code, expected_exception):
    number = "+1234567890"

    mock_verify_sender.side_effect = TwilioRestException(twilio_code)

    with pytest.raises(expected_exception):
        TwilioPhoneProvider().send_verification_sms(number)

    mock_verify_sender.assert_called_once_with(number)


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
