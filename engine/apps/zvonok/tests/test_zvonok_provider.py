from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings

from apps.zvonok.phone_provider import ZvonokPhoneProvider


@pytest.fixture
def provider():
    return ZvonokPhoneProvider()


@pytest.mark.django_db
def test_make_verification_call_with_template_set(provider):
    verification_code = "123456"
    number = "1234567890"
    speaker_id = "Salli"
    template_value = 'Your code is <prosody rate="x-slow">$verification_code</prosody>'
    excepted_message = 'Your code is <prosody rate="x-slow">1   2   3   4   5   6</prosody>'

    with override_settings(ZVONOK_VERIFICATION_TEMPLATE=template_value, ZVONOK_SPEAKER_ID=speaker_id):
        with patch("django.core.cache.cache.set"):
            provider._call_create = MagicMock(return_value=MagicMock(json=lambda: {"call_id": "12345"}))
            provider._generate_verification_code = MagicMock(return_value=verification_code)
            provider.make_verification_call(number)
            provider._call_create.assert_called_once_with(number, excepted_message, speaker_id)


@pytest.mark.django_db
def test_make_verification_call_with_invalid_template_set(provider):
    verification_code = "123456"
    number = "1234567890"
    speaker_id = "Salli"
    template_value = "Your code is"
    excepted_message = "Your code is"

    with override_settings(ZVONOK_VERIFICATION_TEMPLATE=template_value, ZVONOK_SPEAKER_ID=speaker_id):
        with patch("django.core.cache.cache.set"):
            provider._call_create = MagicMock(return_value=MagicMock(json=lambda: {"call_id": "12345"}))
            provider._generate_verification_code = MagicMock(return_value=verification_code)
            provider.make_verification_call(number)
            provider._call_create.assert_called_once_with(number, excepted_message, speaker_id)


@pytest.mark.django_db
def test_make_verification_call_without_template_set(provider):
    verification_code = "123456"
    number = "1234567890"
    speaker_id = "Salli"
    excepted_message = "Your verification code is 1   2   3   4   5   6"
    with override_settings(ZVONOK_SPEAKER_ID=speaker_id):
        with patch("django.core.cache.cache.set"):
            provider._call_create = MagicMock(return_value=MagicMock(json=lambda: {"call_id": "12345"}))
            provider._generate_verification_code = MagicMock(return_value=verification_code)
            provider.make_verification_call(number)
            provider._call_create.assert_called_once_with(number, excepted_message, speaker_id)
