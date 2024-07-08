import logging
from random import randint
from typing import Optional

import requests
from django.core.cache import cache

from apps.base.utils import live_settings
from apps.phone_notifications.exceptions import FailedToMakeCall, FailedToStartVerification
from apps.phone_notifications.phone_provider import PhoneProvider, ProviderFlags
from apps.zvonok.models.phone_call import ZvonokCallStatuses, ZvonokPhoneCall

ZVONOK_CALL_URL = "https://zvonok.com/manager/cabapi_external/api/v1/phones/call/"
ZVONOK_VERIFICATION_CALL_URL = "https://zvonok.com/manager/cabapi_external/api/v1/phones/tellcode/"

logger = logging.getLogger(__name__)


class ZvonokPhoneProvider(PhoneProvider):
    """
    ZvonokPhoneProvider is an implementation of phone provider which supports only voice calls (zvonok.com).
    """

    def make_notification_call(self, number: str, message: str) -> ZvonokPhoneCall:
        speaker = None
        body = None

        if live_settings.ZVONOK_AUDIO_ID:
            message = f'<audio id="{live_settings.ZVONOK_AUDIO_ID}"/>'
        else:
            speaker = live_settings.ZVONOK_SPEAKER_ID

        try:
            response = self._call_create(number, message, speaker)
            response.raise_for_status()
            body = response.json()
            if not body:
                logger.error("ZvonokPhoneProvider.make_notification_call: failed, empty body")
                raise FailedToMakeCall(graceful_msg=f"Failed make notification call to {number}, empty body")
            call_id = body.get("call_id")

            if not call_id:
                logger.error("ZvonokPhoneProvider.make_notification_call: failed, missing call id")
                raise FailedToMakeCall(graceful_msg=self._get_graceful_msg(body, number))

            logger.info(f"ZvonokPhoneProvider.make_notification_call: success, call_id {call_id}")

            return ZvonokPhoneCall(
                status=ZvonokCallStatuses.IN_PROCESS,
                call_id=call_id,
                campaign_id=live_settings.ZVONOK_CAMPAIGN_ID,
            )

        except requests.exceptions.HTTPError as http_err:
            logger.error(f"ZvonokPhoneProvider.make_notification_call: failed {http_err}")
            raise FailedToMakeCall(graceful_msg=self._get_graceful_msg(body, number))
        except (requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError, TypeError) as err:
            logger.error(f"ZvonokPhoneProvider.make_notification_call: failed {err}")
            raise FailedToMakeCall(graceful_msg=f"Failed make notification call to {number}")

    def make_call(self, number: str, message: str):
        body = None
        speaker = live_settings.ZVONOK_SPEAKER_ID

        try:
            response = self._call_create(number, message, speaker)
            response.raise_for_status()
            body = response.json()
            if not body:
                logger.error("ZvonokPhoneProvider.make_call: failed, empty body")
                raise FailedToMakeCall(graceful_msg=f"Failed make call to {number}, empty body")

            call_id = body.get("call_id")

            if not call_id:
                raise FailedToMakeCall(graceful_msg=self._get_graceful_msg(body, number))
            logger.info(f"ZvonokPhoneProvider.make_call: success, call_id {call_id}")

        except requests.exceptions.HTTPError as http_err:
            logger.error(f"ZvonokPhoneProvider.make_call: failed {http_err}")
            raise FailedToMakeCall(graceful_msg=self._get_graceful_msg(body, number))
        except (requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError, TypeError) as err:
            logger.error(f"ZvonokPhoneProvider.make_call: failed {err}")
            raise FailedToMakeCall(graceful_msg=f"Failed make call to {number}")

    def _call_create(self, number: str, text: str, speaker: Optional[str] = None):
        params = {
            "public_key": live_settings.ZVONOK_API_KEY,
            "campaign_id": live_settings.ZVONOK_CAMPAIGN_ID,
            "phone": number,
            "text": text,
        }

        if speaker:
            params["speaker"] = speaker

        return requests.post(ZVONOK_CALL_URL, params=params)

    def _verification_call_create(self, number: str, code: int):
        params = {
            "public_key": live_settings.ZVONOK_API_KEY,
            "campaign_id": live_settings.ZVONOK_VERIFICATION_CAMPAIGN_ID,
            "phone": number,
            "pincode": code,
        }
        return requests.post(ZVONOK_VERIFICATION_CALL_URL, params=params)

    def _get_graceful_msg(self, body, number):
        if body:
            status = body.get("status")
            data = body.get("data")
            if status == "error" and data:
                return f"Failed make call to {number} with error: {data}"
        return f"Failed make call to {number}"

    def make_verification_call(self, number: str):
        body = None
        code = self._generate_verification_code()
        cache.set(self._cache_key(number), code, timeout=10 * 60)

        if not live_settings.ZVONOK_VERIFICATION_CAMPAIGN_ID:
            raise FailedToStartVerification(
                graceful_msg="Failed make verification call, verification campaign id not set."
            )

        try:
            response = self._verification_call_create(number, code)
            body = response.json()
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"ZvonokPhoneProvider.make_verification_call: failed {http_err}")
            raise FailedToStartVerification(graceful_msg=self._get_graceful_msg(body, number))
        except (requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError, TypeError) as err:
            logger.error(f"ZvonokPhoneProvider.make_verification_call: failed {err}")
            raise FailedToStartVerification(graceful_msg=f"Failed make verification call to {number}")

    def finish_verification(self, number, code):
        has = cache.get(self._cache_key(number))
        if has is not None and has == code:
            return number
        else:
            return None

    def _cache_key(self, number):
        return f"zvonok_provider_{number}"

    def _generate_verification_code(self):
        return str(randint(100000, 999999))

    @property
    def flags(self) -> ProviderFlags:
        return ProviderFlags(
            configured=True,
            test_sms=False,
            test_call=True,
            verification_call=True,
            verification_sms=False,
        )
