import pytest

from apps.twilioapp.tests.factories import (
    TwilioAccountFactory,
    TwilioPhoneCallSenderFactory,
    TwilioSmsSenderFactory,
    TwilioVerificationSenderFactory,
)


@pytest.fixture
def make_twilio_account():
    def _make_twilio_account(**kwargs):
        return TwilioAccountFactory(**kwargs)

    return _make_twilio_account


@pytest.fixture
def make_twilio_phone_call_sender():
    def _make_twilio_phone_call_sender(**kwargs):
        return TwilioPhoneCallSenderFactory(**kwargs)

    return _make_twilio_phone_call_sender


@pytest.fixture
def make_twilio_sms_sender():
    def _make_twilio_sms_sender(**kwargs):
        return TwilioSmsSenderFactory(**kwargs)

    return _make_twilio_sms_sender


@pytest.fixture
def make_twilio_verification_sender():
    def _make_twilio_verification_sender(**kwargs):
        return TwilioVerificationSenderFactory(**kwargs)

    return _make_twilio_verification_sender
