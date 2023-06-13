from unittest.mock import patch

import pytest

from apps.base.models import LiveSetting
from apps.base.utils import live_settings
from apps.twilioapp.phone_provider import TwilioPhoneProvider


@pytest.mark.django_db
def test_fallback_to_settings(settings):
    settings.SOME_NEW_FEATURE_ENABLED = True

    with patch.object(LiveSetting, "AVAILABLE_NAMES", ("SOME_NEW_FEATURE_ENABLED",)):
        assert LiveSetting.get_setting("SOME_NEW_FEATURE_ENABLED") is True


@pytest.mark.django_db
def test_take_from_db(settings):
    settings.SOME_NEW_FEATURE_ENABLED = True

    with patch.object(LiveSetting, "AVAILABLE_NAMES", ("SOME_NEW_FEATURE_ENABLED",)):
        LiveSetting.objects.create(name="SOME_NEW_FEATURE_ENABLED", value=False)
        assert LiveSetting.get_setting("SOME_NEW_FEATURE_ENABLED") is False


@pytest.mark.django_db
def test_restrict_foreign_names():
    with pytest.raises(ValueError):
        LiveSetting.objects.create(name="SOME_NONEXISTENT_FANCY_FEATURE_ENABLED", value=42)

    with pytest.raises(ValueError):
        LiveSetting.get_setting("SOME_NONEXISTENT_FANCY_FEATURE_ENABLED")


@pytest.mark.parametrize("value", (True, None, 12, "test string", ["hey", "there", 1]))
@pytest.mark.django_db
def test_multi_type_support(value):
    with patch.object(LiveSetting, "AVAILABLE_NAMES", ("SOME_NEW_FEATURE_ENABLED",)):
        LiveSetting.objects.create(name="SOME_NEW_FEATURE_ENABLED", value=value)
        setting_value = LiveSetting.get_setting("SOME_NEW_FEATURE_ENABLED")

        assert type(setting_value) == type(value)
        assert setting_value == value


@pytest.mark.django_db
def test_live_settings_proxy(settings, monkeypatch):
    settings.SOME_SETTING = 12
    monkeypatch.setattr(LiveSetting, "AVAILABLE_NAMES", ("SOME_SETTING",))
    assert live_settings.SOME_SETTING == 12

    live_settings.SOME_SETTING = 42
    assert LiveSetting.objects.get(name="SOME_SETTING").value == 42
    assert live_settings.SOME_SETTING == 42


@pytest.mark.django_db
def test_twilio_respects_changed_credentials(settings):
    settings.TWILIO_ACCOUNT_SID = "twilio_account_sid"
    settings.TWILIO_AUTH_TOKEN = "twilio_auth_token"
    settings.TWILIO_NUMBER = "twilio_number"

    twilio_client = TwilioPhoneProvider()

    live_settings.TWILIO_ACCOUNT_SID = "new_twilio_account_sid"
    live_settings.TWILIO_AUTH_TOKEN = "new_twilio_auth_token"
    live_settings.TWILIO_NUMBER = "new_twilio_number"

    assert twilio_client._default_twilio_api_client.username == "new_twilio_account_sid"
    assert twilio_client._default_twilio_api_client.password == "new_twilio_auth_token"
    assert twilio_client._default_twilio_number == "new_twilio_number"
