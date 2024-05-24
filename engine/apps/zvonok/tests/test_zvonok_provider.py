from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings

from apps.phone_notifications.exceptions import FailedToStartVerification
from apps.zvonok.phone_provider import ZvonokPhoneProvider


@pytest.fixture
def provider():
    return ZvonokPhoneProvider()


@pytest.mark.django_db
def test_make_verification_call(provider):
    verification_code = "123456789"
    number = "1234567890"
    campaign_id = "123456"
    with override_settings(ZVONOK_VERIFICATION_CAMPAIGN_ID=campaign_id):
        with patch("django.core.cache.cache.set"):
            provider._verification_call_create = MagicMock(return_value=MagicMock(json=lambda: {"status": "ok"}))
            provider._generate_verification_code = MagicMock(return_value=verification_code)
            provider.make_verification_call(number)
            provider._verification_call_create.assert_called_once_with(number, verification_code)


@pytest.mark.django_db
def test_make_verification_call_without_campaign_id(provider):
    number = "1234567890"
    with patch("django.core.cache.cache.set"):
        with pytest.raises(FailedToStartVerification):
            provider.make_verification_call(number)


@pytest.mark.django_db
def test_make_verification_call_with_error(provider):
    number = "1234567890"
    campaign_id = "123456"

    with override_settings(ZVONOK_VERIFICATION_CAMPAIGN_ID=campaign_id):
        with patch("django.core.cache.cache.set"):
            with pytest.raises(FailedToStartVerification):
                provider._verification_call_create = MagicMock(
                    return_value=MagicMock(
                        json={"status": "error", "data": "Form isn't valid: * campaign_id\n  * Invalid campaign type"}
                    )
                )
                provider.make_verification_call(number)
