from unittest.mock import patch

import pytest
from django.conf import settings

from apps.twilioapp.phone_provider import TwilioPhoneProvider

US_VERIFY = "us_verify"
US_SMS = "us_sms"
US_PHONE = "us_phone"

DB_DEFAULT_VERIFY = "db_default_verify"
DB_DEFAULT_SMS = "db_default_sms"
DB_DEFAULT_PHONE = "db_default_phone"

DB_TWILIO_AUTH_TOKEN = "db_twilio_account_auth_token"
DB_TWILIO_ACCOUNT_SID = "db_twilio_account_sid"

ENV_VERIFY_SERVICE_SID = "env_twilio_verify_service_sid"
ENV_TWILIO_NUMBER = "env_twilio_number"
ENV_TWILIO_AUTH_TOKEN = "env_twilio_auth_token"
ENV_TWILIO_ACCOUNT_SID = "env_twilio_account_sid"


@pytest.fixture
def setup_env_default_twilio():
    settings.TWILIO_ACCOUNT_SID = ENV_TWILIO_ACCOUNT_SID
    settings.TWILIO_AUTH_TOKEN = ENV_TWILIO_AUTH_TOKEN
    settings.TWILIO_NUMBER = ENV_TWILIO_NUMBER
    settings.TWILIO_VERIFY_SERVICE_SID = ENV_VERIFY_SERVICE_SID


@pytest.fixture
def setup_db_default_account(make_twilio_account):
    return make_twilio_account(
        name="DB Twilio Account", account_sid=DB_TWILIO_ACCOUNT_SID, auth_token=DB_TWILIO_AUTH_TOKEN
    )


@pytest.fixture
def setup_default_senders(
    setup_db_default_account, make_twilio_phone_call_sender, make_twilio_sms_sender, make_twilio_verification_sender
):
    make_twilio_phone_call_sender(name="Default", number=DB_DEFAULT_PHONE, account=setup_db_default_account)
    make_twilio_sms_sender(name="Default", sender=DB_DEFAULT_SMS, account=setup_db_default_account)
    make_twilio_verification_sender(
        name="Default", verify_service_sid=DB_DEFAULT_VERIFY, account=setup_db_default_account
    )


@pytest.fixture
def setup_us_senders(
    setup_db_default_account, make_twilio_phone_call_sender, make_twilio_sms_sender, make_twilio_verification_sender
):
    make_twilio_phone_call_sender(name="US/Canada", country_code="1", number=US_PHONE, account=setup_db_default_account)
    make_twilio_sms_sender(name="US/Canada", country_code="1", sender=US_SMS, account=setup_db_default_account)
    make_twilio_verification_sender(
        name="US/Canada", country_code="1", verify_service_sid=US_VERIFY, account=setup_db_default_account
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "sender,expected_from",
    [
        (TwilioPhoneProvider._phone_sender, ENV_TWILIO_NUMBER),
        (TwilioPhoneProvider._sms_sender, ENV_TWILIO_NUMBER),
        (TwilioPhoneProvider._verify_sender, ENV_VERIFY_SERVICE_SID),
    ],
)
def test_use_env_default_senders(
    setup_env_default_twilio,
    setup_us_senders,
    make_twilio_account,
    make_twilio_phone_call_sender,
    make_twilio_sms_sender,
    make_twilio_verification_sender,
    sender,
    expected_from,
):
    with patch(
        "apps.twilioapp.phone_provider.TwilioPhoneProvider._parse_number",
        return_value=(True, None, "44"),
    ):
        provider = TwilioPhoneProvider()
        client, _from = sender(provider, "")
        assert _from == expected_from
        assert client.username == ENV_TWILIO_ACCOUNT_SID
        assert client.password == ENV_TWILIO_AUTH_TOKEN


@pytest.mark.django_db
@pytest.mark.parametrize(
    "sender,expected_from",
    [
        (TwilioPhoneProvider._phone_sender, DB_DEFAULT_PHONE),
        (TwilioPhoneProvider._sms_sender, DB_DEFAULT_SMS),
        (TwilioPhoneProvider._verify_sender, DB_DEFAULT_VERIFY),
    ],
)
def test_use_db_default_senders(
    setup_env_default_twilio,
    setup_default_senders,
    make_twilio_account,
    make_twilio_phone_call_sender,
    make_twilio_sms_sender,
    make_twilio_verification_sender,
    sender,
    expected_from,
):
    with patch(
        "apps.twilioapp.phone_provider.TwilioPhoneProvider._parse_number",
        return_value=(True, None, "44"),
    ):
        provider = TwilioPhoneProvider()
        client, _from = sender(provider, "")
        assert _from == expected_from
        assert client.username == DB_TWILIO_ACCOUNT_SID
        assert client.password == DB_TWILIO_AUTH_TOKEN


@pytest.mark.django_db
@pytest.mark.parametrize(
    "sender,expected_from",
    [
        (TwilioPhoneProvider._phone_sender, US_PHONE),
        (TwilioPhoneProvider._sms_sender, US_SMS),
        (TwilioPhoneProvider._verify_sender, US_VERIFY),
    ],
)
def test_use_country_code_senders(
    setup_env_default_twilio,
    setup_default_senders,
    setup_us_senders,
    make_twilio_account,
    make_twilio_phone_call_sender,
    make_twilio_sms_sender,
    make_twilio_verification_sender,
    sender,
    expected_from,
):
    with patch(
        "apps.twilioapp.phone_provider.TwilioPhoneProvider._parse_number",
        return_value=(True, None, "1"),
    ):
        provider = TwilioPhoneProvider()
        client, _from = sender(provider, "")
        assert _from == expected_from
        assert client.username == DB_TWILIO_ACCOUNT_SID
        assert client.password == DB_TWILIO_AUTH_TOKEN
