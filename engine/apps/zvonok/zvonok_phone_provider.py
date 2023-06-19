import logging
import requests
import os

from random import randint

from django.core.cache import cache

from apps.base.models import LiveSetting
from apps.base.utils import live_settings

from apps.phone_notifications.exceptions import (
    FailedToFinishVerification,
    FailedToMakeCall,
    FailedToSendSMS,
    FailedToStartVerification,
)
from apps.phone_notifications.phone_provider import PhoneProvider, ProviderFlags

ZVONOK_CALL_URL = 'https://zvonok.com/manager/cabapi_external/api/v1/phones/call/'
ZVONOK_TIMEOUT = os.environ.get("ZVONOK_TIMEOUT", default="30")
ZVONOK_SPEAKER = os.environ.get("ZVONOK_SPEAKER", default="Joanna")

logger = logging.getLogger(__name__)

class ZvonokPhoneProvider(PhoneProvider):
    """
    ZvonokPhoneProvider is an implementation of phone provider which supports only voice calls (zvonok.com).
    """

    def make_notification_call(self, number, message):
        logger.info(f"ZvonokProvider.make_notification_call to number: {number}")
        try:
            response = self._create_call(number, message)
            response_json = response.json()
            if response_json['status'] == 'error':
                logger.error(f"ZvonokPhoneProvider.make_notification_call FAILED to number: {number}")
                raise FailedToStartVerification
        except RequestException as e:
            logger.error(f"ZvonokPhoneProvider.make_verification_call: failed {e}")
            raise FailedToStartVerification

    def make_call(self, number: str, message: str):
        logger.info(f"ZvonokPhoneProvider.make_call to number: {number}")
        try:
            response = self._create_call(number, message)
            response_json = response.json()
            if response_json['status'] == 'error':
                logger.error(f"ZvonokPhoneProvider.make_call FAILED to number: {number}")
                raise FailedToMakeCall
        except RequestException as e:
            logger.error(f"ZvonokPhoneProvider.make_call: failed {e}")
            raise FailedToMakeCall

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

    def _create_call(self, number, message):
        url = ZVONOK_CALL_URL
        payload={'public_key': ZVONOK_API_KEY,
        'phone': number,
        'campaign_id': ZVONOK_CALL_CAMPAIGN_ID,
        'text': message,
        'speaker': ZVONOK_SPEAKER}
        response = requests.request("POST", url, data=payload, timeout=ZVONOK_TIMEOUT)
        return response

    @property
    def flags(self) -> ProviderFlags:
        return ProviderFlags(
            configured=True,
            test_sms=False,
            test_call=True,
            verification_call=True,
            verification_sms=False,
        )
