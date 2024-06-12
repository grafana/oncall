import logging
from random import randint
from string import Template

import requests
from django.core.cache import cache
from requests.auth import HTTPBasicAuth

from apps.base.models import LiveSetting
from apps.base.utils import live_settings
from apps.exotel.models.phone_call import ExotelCallStatuses, ExotelPhoneCall
from apps.exotel.status_callback import get_call_status_callback_url
from apps.phone_notifications.exceptions import FailedToMakeCall, FailedToStartVerification
from apps.phone_notifications.phone_provider import PhoneProvider, ProviderFlags

EXOTEL_ENDPOINT = "https://twilix.exotel.com/v1/Accounts/"
EXOTEL_SMS_API = "/Sms/send.json"
EXOTEL_CALL_API = "/Calls/connect.json"

logger = logging.getLogger(__name__)


class ExotelPhoneProvider(PhoneProvider):
    """
    ExotelPhoneProvider is an implementation of phone provider (exotel.com).
    """

    def make_notification_call(self, number: str, message: str) -> ExotelPhoneCall:
        body = None
        try:
            response = self._call_create(number)
            response.raise_for_status()
            body = response.json()
            if not body:
                logger.error("ExotelPhoneProvider.make_notification_call: failed, empty body")
                raise FailedToMakeCall(graceful_msg=f"Failed make notification call to {number}, empty body")

            sid = body.get("Call").get("Sid")

            if not sid:
                logger.error("ExotelPhoneProvider.make_notification_call: failed, missing sid")
                raise FailedToMakeCall(graceful_msg=f"Failed make notification call to {number} missing sid")

            logger.info(f"ExotelPhoneProvider.make_notification_call: success, sid {sid}")

            return ExotelPhoneCall(
                status=ExotelCallStatuses.IN_PROGRESS,
                call_id=sid,
            )

        except requests.exceptions.HTTPError as http_err:
            logger.error(f"ExotelPhoneProvider.make_notification_call: failed {http_err}")
            raise FailedToMakeCall(graceful_msg=f"Failed make notification call to {number} http error")
        except (requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError, TypeError) as err:
            logger.error(f"ExotelPhoneProvider.make_notification_call: failed {err}")
            raise FailedToMakeCall(graceful_msg=f"Failed make notification call to {number}")

    def make_call(self, number: str, message: str):
        body = None

        try:
            response = self._call_create(number, False)
            response.raise_for_status()
            body = response.json()
            if not body:
                logger.error("ExotelPhoneProvider.make_call: failed, empty body")
                raise FailedToMakeCall(graceful_msg=f"Failed make call to {number}, empty body")

            sid = body.get("Call").get("Sid")

            if not sid:
                logger.error("ExotelPhoneProvider.make_call: failed, missing sid")
                raise FailedToMakeCall(graceful_msg=f"Failed make call to {number} missing sid")

            logger.info(f"ExotelPhoneProvider.make_call: success, sid {sid}")

        except requests.exceptions.HTTPError as http_err:
            logger.error(f"ExotelPhoneProvider.make_call: failed {http_err}")
            raise FailedToMakeCall(graceful_msg=f"Failed make call to {number} http error")
        except (requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError, TypeError) as err:
            logger.error(f"ExotelPhoneProvider.make_call: failed {err}")
            raise FailedToMakeCall(graceful_msg=f"Failed make call to {number}")

    def _call_create(self, number: str, with_callback: bool = True):
        params = {
            "From": number,
            "CallerId": live_settings.EXOTEL_CALLER_ID,
            "Url": f"http://my.exotel.in/exoml/start/{live_settings.EXOTEL_APP_ID}",
        }

        if with_callback:
            params.update(
                {
                    "StatusCallback": get_call_status_callback_url(),
                    "StatusCallbackContentType": "application/json",
                }
            )

        auth = HTTPBasicAuth(live_settings.EXOTEL_API_KEY, live_settings.EXOTEL_API_TOKEN)

        exotel_call_url = f"{EXOTEL_ENDPOINT}{live_settings.EXOTEL_ACCOUNT_SID}{EXOTEL_CALL_API}"

        return requests.post(exotel_call_url, auth=auth, params=params)

    def _get_graceful_msg(self, body, number):
        if body:
            status = body.get("SMSMessage").get("Status")
            data = body.get("SMSMessage").get("DetailedStatus")
            if status == "failed" and data:
                return f"Failed sending sms to {number} with error: {data}"
        return f"Failed sending sms to {number}"

    def send_verification_sms(self, number: str):
        code = self._generate_verification_code()
        cache.set(self._cache_key(number), code, timeout=10 * 60)

        body = None
        message = Template(live_settings.EXOTEL_SMS_VERIFICATION_TEMPLATE).safe_substitute(verification_code=code)
        try:
            response = self._send_verification_code(
                number,
                message,
            )
            response.raise_for_status()
            body = response.json()
            if not body:
                logger.error("ExotelPhoneProvider.send_verification_sms: failed, empty body")
                raise FailedToStartVerification(graceful_msg=f"Failed sending verification sms to {number}, empty body")

            sid = body.get("SMSMessage").get("Sid")
            if not sid:
                raise FailedToStartVerification(graceful_msg=self._get_graceful_msg(body, number))
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"ExotelPhoneProvider.send_verification_sms: failed {http_err}")
            raise FailedToStartVerification(graceful_msg=self._get_graceful_msg(body, number))
        except (requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError, TypeError) as err:
            logger.error(f"ExotelPhoneProvider.send_verification_sms: failed {err}")
            raise FailedToStartVerification(graceful_msg=f"Failed sending verification SMS to {number}")

    def _send_verification_code(self, number: str, body: str):
        params = {
            "From": live_settings.EXOTEL_SMS_SENDER_ID,
            "DltEntityId": live_settings.EXOTEL_SMS_DLT_ENTITY_ID,
            "To": number,
            "Body": body,
        }

        auth = HTTPBasicAuth(live_settings.EXOTEL_API_KEY, live_settings.EXOTEL_API_TOKEN)

        exotel_sms_url = f"{EXOTEL_ENDPOINT}{live_settings.EXOTEL_ACCOUNT_SID}{EXOTEL_SMS_API}"

        return requests.post(exotel_sms_url, auth=auth, params=params)

    def finish_verification(self, number, code):
        has = cache.get(self._cache_key(number))
        if has is not None and has == code:
            return number
        else:
            return None

    def _cache_key(self, number):
        return f"exotel_provider_{number}"

    def _generate_verification_code(self):
        return str(randint(100000, 999999))

    @property
    def flags(self) -> ProviderFlags:
        return ProviderFlags(
            configured=not LiveSetting.objects.filter(name__startswith="EXOTEL", error__isnull=False).exists(),
            test_sms=False,
            test_call=True,
            verification_call=False,
            verification_sms=True,
        )
