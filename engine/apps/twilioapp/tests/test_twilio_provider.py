from unittest import mock

import pytest
from twilio.base.exceptions import TwilioRestException

from apps.phone_notifications.exceptions import FailedToFinishVerification, FailedToMakeCall, FailedToSendSMS
from apps.twilioapp.phone_provider import TwilioPhoneProvider


class MockTwilioCallInstance:
    status = "mock_status"
    sid = "mock_sid"


class MockTwilioMessageInstance:
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


TEST_NUMBER = "+1234567890"
TEST_MESSAGE = "Hello"
TEST_CODE = "12345"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "twilio_code,expected_exception,graceful_msg,provider_method,mock_method",
    [
        (60200, FailedToMakeCall, True, lambda p: p.make_call(TEST_NUMBER, TEST_MESSAGE), "_call_create"),
        (30808, FailedToMakeCall, False, lambda p: p.make_call(TEST_NUMBER, TEST_MESSAGE), "_call_create"),
        (None, FailedToMakeCall, False, lambda p: p.make_call(TEST_NUMBER, TEST_MESSAGE), "_call_create"),
        (30410, FailedToMakeCall, True, lambda p: p.make_notification_call(TEST_NUMBER, TEST_MESSAGE), "_call_create"),
        (30808, FailedToMakeCall, False, lambda p: p.make_notification_call(TEST_NUMBER, TEST_MESSAGE), "_call_create"),
        (None, FailedToMakeCall, False, lambda p: p.make_notification_call(TEST_NUMBER, TEST_MESSAGE), "_call_create"),
        (30004, FailedToSendSMS, True, lambda p: p.send_sms(TEST_NUMBER, TEST_MESSAGE), "_messages_create"),
        (30808, FailedToSendSMS, False, lambda p: p.send_sms(TEST_NUMBER, TEST_MESSAGE), "_messages_create"),
        (None, FailedToSendSMS, False, lambda p: p.send_sms(TEST_NUMBER, TEST_MESSAGE), "_messages_create"),
        (
            30006,
            FailedToSendSMS,
            True,
            lambda p: p.send_notification_sms(TEST_NUMBER, TEST_MESSAGE),
            "_messages_create",
        ),
        (
            30808,
            FailedToSendSMS,
            False,
            lambda p: p.send_notification_sms(TEST_NUMBER, TEST_MESSAGE),
            "_messages_create",
        ),
        (
            None,
            FailedToSendSMS,
            False,
            lambda p: p.send_notification_sms(TEST_NUMBER, TEST_MESSAGE),
            "_messages_create",
        ),
        (
            60203,
            FailedToFinishVerification,
            True,
            lambda p: p.finish_verification(TEST_NUMBER, TEST_CODE),
            "_verify_sender",
        ),
        (
            30808,
            FailedToFinishVerification,
            False,
            lambda p: p.finish_verification(TEST_NUMBER, TEST_CODE),
            "_verify_sender",
        ),
        (
            None,
            FailedToFinishVerification,
            False,
            lambda p: p.finish_verification(TEST_NUMBER, TEST_CODE),
            "_verify_sender",
        ),
    ],
)
@mock.patch("apps.twilioapp.phone_provider.TwilioPhoneProvider._normalize_phone_number", return_value=(TEST_NUMBER, 1))
def test_twilio_provider_exceptions(
    mocked_normalize, twilio_code, expected_exception, graceful_msg, provider_method, mock_method
):
    provider = TwilioPhoneProvider()

    with mock.patch(f"apps.twilioapp.phone_provider.TwilioPhoneProvider.{mock_method}") as twilio_mock:
        twilio_mock.side_effect = TwilioRestException(500, "", code=twilio_code)
        with pytest.raises(expected_exception) as exc:
            provider_method(provider)
            if graceful_msg:
                assert len(exc.value.graceful_msg) > 0
            else:
                assert exc.value.graceful_msg is None
        twilio_mock.assert_called_once()


class MockTwilioSMSInstance:
    status = "mock_status"
    sid = "mock_sid"
