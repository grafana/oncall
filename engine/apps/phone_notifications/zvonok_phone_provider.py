import requests
import os

from random import randint

from django.core.cache import cache

from apps.base.models import LiveSetting
from apps.base.utils import live_settings

from .phone_provider import PhoneProvider, ProviderFlags

ZVONOK_CALL_URL = 'https://zvonok.com/manager/cabapi_external/api/v1/phones/call/'

class ZvonokPhoneProvider(PhoneProvider):
    """
    ZvonokPhoneProvider is an implementation of phone provider which supports only voice calls (zvonok.com).
    API docs: https://api-docs.zvonok.com/ . Call status description: https://zvonok.com/ru-ru/guide/guide_statuses/
    """

    def make_notification_call(self, number, message):
        url = ZVONOK_CALL_URL
        payload={'public_key': ZVONOK_API_KEY,
        'phone': number,
        'campaign_id': ZVONOK_CALL_CAMPAIGN_ID,
        'text': message,
        'speaker': 'Joanna'}
        response = requests.request("POST", url, data=payload)
        call_id = response.json().get("call_id")
        print(f'call_id: {call_id}')

    def make_call(self, number: str, message: str):
        url = ZVONOK_CALL_URL
        payload={'public_key': ZVONOK_API_KEY,
        'phone': number,
        'campaign_id': ZVONOK_CALL_CAMPAIGN_ID,
        'text': message,
        'speaker': 'Joanna'}
        response = requests.request("POST", url, data=payload)
        print(response.text)
        print(f'ZvonokPhoneProvider.make_call: Make call with message "{message}" to {number}')

    def make_verification_call(self, number: str):
        code = str(randint(100000, 999999))
        cache.set(self._cache_key(number), code, timeout=10 * 60)
        codewspaces = " ".join(code)
        self.make_call(number, f"Your verification code is {codewspaces}")

    def finish_verification(self, number, code):
        has = cache.get(self._cache_key(number))
        if has is not None and has == code:
            return number
        else:
            return None

    def _cache_key(self, number):
        return f"zvonok_provider_{number}"

    @property
    def flags(self) -> ProviderFlags:
        return ProviderFlags(
            configured=True,
            test_sms=False,
            test_call=True,
            verification_call=True,
            verification_sms=False,
        )
