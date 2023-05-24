import logging
import urllib.parse
from string import digits

from phonenumbers import COUNTRY_CODE_TO_REGION_CODE
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from apps.base.models import LiveSetting
from apps.base.utils import live_settings
from apps.phone_notifications.exceptions import (
    FailedToFinishVerification,
    FailedToMakeCall,
    FailedToSendSMS,
    FailedToStartVerification,
)
from apps.phone_notifications.phone_provider import PhoneProvider, ProviderFlags
from apps.twilioapp.gather import get_gather_message, get_gather_url
from apps.twilioapp.models import TwilioCallStatuses, TwilioPhoneCall, TwilioSMS
from apps.twilioapp.status_callback import get_call_status_callback_url, get_sms_status_callback_url

logger = logging.getLogger(__name__)


class TwilioPhoneProvider(PhoneProvider):
    def make_notification_call(self, number: str, message: str) -> TwilioPhoneCall:
        message = self._escape_call_message(message)

        twiml_query = self._message_to_twiml(message, with_gather=True)

        response = None
        try_without_callback = False

        try:
            response = self._call_create(twiml_query, number, with_callback=True)
        except TwilioRestException as e:
            # If status callback is not valid and not accessible from public url then trying to send message without it
            # https://www.twilio.com/docs/api/errors/21609
            if e.code == 21609:
                logger.info(f"TwilioPhoneProvider.make_notification_call: error 21609, calling without callback_url")
                try_without_callback = True
            else:
                logger.error(f"TwilioPhoneProvider.make_notification_call: failed {e}")
                raise FailedToMakeCall

        if try_without_callback:
            try:
                response = self._call_create(twiml_query, number, with_callback=False)
            except TwilioRestException as e:
                logger.error(f"TwilioPhoneProvider.make_notification_call: failed {e}")
                raise FailedToMakeCall

        if response and response.status and response.sid:
            return TwilioPhoneCall(
                status=TwilioCallStatuses.DETERMINANT.get(response.status, None),
                sid=response.sid,
            )

    def send_notification_sms(self, number: str, message: str) -> TwilioSMS:
        try_without_callback = False
        response = None

        try:
            response = self._messages_create(number, message, with_callback=True)
        except TwilioRestException as e:
            # If status callback is not valid and not accessible from public url then trying to send message without it
            # https://www.twilio.com/docs/api/errors/21609
            if e.code == 21609:
                logger.info(f"TwilioPhoneProvider.send_notification_sms: error 21609, sending without callback_url")
                try_without_callback = True
            else:
                logger.error(f"TwilioPhoneProvider.send_notification_sms: failed {e}")
                raise FailedToSendSMS

        if try_without_callback:
            try:
                response = self._messages_create(number, message, with_callback=False)
            except TwilioRestException as e:
                logger.error(f"TwilioPhoneProvider.send_notification_sms: failed {e}")
                raise FailedToSendSMS

        if response and response.status and response.sid:
            return TwilioSMS(
                status=TwilioCallStatuses.DETERMINANT.get(response.status, None),
                sid=response.sid,
            )

    def send_verification_sms(self, number: str):
        self._send_verification_code(number, via="sms")

    def finish_verification(self, number: str, code: str):
        # I'm not sure if we need verification_and_parse via twilio pipeline here
        # Verification code anyway is sent to not verified phone number.
        # Just leaving it as it was before phone_provider refactoring.
        normalized_number, _ = self._normalize_phone_number(number)
        if normalized_number:
            try:
                verification_check = self._twilio_api_client.verify.services(
                    live_settings.TWILIO_VERIFY_SERVICE_SID
                ).verification_checks.create(to=normalized_number, code=code)
                logger.info(f"TwilioPhoneProvider.finish_verification: verification_status {verification_check.status}")
                if verification_check.status == "approved":
                    return normalized_number
            except TwilioRestException as e:
                logger.error(f"TwilioPhoneProvider.finish_verification: failed to verify number {number}: {e}")
                raise FailedToFinishVerification
        else:
            return None

    def make_call(self, number: str, message: str):
        twiml_query = self._message_to_twiml(message, with_gather=False)
        try:
            self._call_create(twiml_query, number, with_callback=False)
        except TwilioRestException as e:
            logger.error(f"TwilioPhoneProvider.make_call: failed {e}")
            raise FailedToMakeCall

    def send_sms(self, number: str, message: str):
        try:
            self._messages_create(number, message, with_callback=False)
        except TwilioRestException as e:
            logger.error(f"TwilioPhoneProvider.send_sms: failed {e}")
            raise FailedToSendSMS

    def _message_to_twiml(self, message: str, with_gather=False):
        q = f"<Response><Say>{message}</Say></Response>"
        if with_gather:
            gather_subquery = f'<Gather numDigits="1" action="{get_gather_url()}" method="POST"><Say>{get_gather_message()}</Say></Gather>'
            q = f"<Response><Say>{message}</Say>{gather_subquery}</Response>"
        return urllib.parse.quote(
            q,
            safe="",
        )

    def _call_create(self, twiml_query: str, to: str, with_callback: bool):
        url = "http://twimlets.com/echo?Twiml=" + twiml_query
        if with_callback:
            status_callback = get_call_status_callback_url()
            status_callback_events = ["initiated", "ringing", "answered", "completed"]
            return self._twilio_api_client.calls.create(
                url=url,
                to=to,
                from_=self._twilio_number,
                method="GET",
                status_callback=status_callback,
                status_callback_event=status_callback_events,
                status_callback_method="POST",
            )
        else:
            return self._twilio_api_client.calls.create(
                url=url,
                to=to,
                from_=self._twilio_number,
                method="GET",
            )

    def _messages_create(self, number: str, text: str, with_callback: bool):
        if with_callback:
            status_callback = get_sms_status_callback_url()
            return self._twilio_api_client.messages.create(
                body=text, to=number, from_=self._twilio_number, status_callback=status_callback
            )
        else:
            return self._twilio_api_client.messages.create(
                body=text,
                to=number,
                from_=self._twilio_number,
            )

    def _send_verification_code(self, number: str, via: str):
        # https://www.twilio.com/docs/verify/api/verification?code-sample=code-start-a-verification-with-sms&code-language=Python&code-sdk-version=6.x
        try:
            verification = self._twilio_api_client.verify.services(
                live_settings.TWILIO_VERIFY_SERVICE_SID
            ).verifications.create(to=number, channel=via)
            logger.info(f"TwilioPhoneProvider._send_verification_code: verification status {verification.status}")
        except TwilioRestException as e:
            logger.error(f"Twilio verification start error: {e} to number {number}")
            raise FailedToStartVerification

    def _normalize_phone_number(self, number: str):
        # TODO: phone_provider: is it best place to parse phone number?
        number = self._parse_phone_number(number)

        # Verify and parse phone number with Twilio API
        normalized_phone_number = None
        country_code = None
        if number != "" and number != "+":
            try:
                ok, normalized_phone_number, country_code = self._parse_number(number)
                if normalized_phone_number == "":
                    normalized_phone_number = None
                    country_code = None
                if not ok:
                    normalized_phone_number = None
                    country_code = None
            except TypeError:
                return None, None

        return normalized_phone_number, country_code

    # Use responsibly
    def _parse_number(self, number: str):
        try:
            response = self._twilio_api_client.lookups.phone_numbers(number).fetch()
            return True, response.phone_number, self._get_calling_code(response.country_code)
        except TwilioRestException as e:
            if e.code == 20404:
                # Not sure, why 20404 (NotFound according to TwilioDocs) handled gracefully, leaving it as it is.
                # https://www.twilio.com/docs/api/errors/20404"
                return False, None, None
            if e.code == 20003:
                raise e
        except KeyError as e:
            # Don't know why KeyError is gracefully handled here, probably exception raised by twilio_client.
            logger.info(f"twilio_client._parse_number: Gracefully handle KeyError: {e}")
            return False, None, None

    @property
    def _twilio_api_client(self):
        if live_settings.TWILIO_API_KEY_SID and live_settings.TWILIO_API_KEY_SECRET:
            return Client(
                live_settings.TWILIO_API_KEY_SID, live_settings.TWILIO_API_KEY_SECRET, live_settings.TWILIO_ACCOUNT_SID
            )
        else:
            return Client(live_settings.TWILIO_ACCOUNT_SID, live_settings.TWILIO_AUTH_TOKEN)

    def _get_calling_code(self, iso):
        for code, isos in COUNTRY_CODE_TO_REGION_CODE.items():
            if iso.upper() in isos:
                return code
        return None

    @property
    def _twilio_number(self):
        return live_settings.TWILIO_NUMBER

    def _escape_call_message(self, message):
        # https://www.twilio.com/docs/api/errors/12100
        message = message.replace("&", "&amp;")
        message = message.replace(">", "&gt;")
        message = message.replace("<", "&lt;")
        return message

    def _parse_phone_number(self, raw_phone_number):
        return "+" + "".join(c for c in raw_phone_number if c in digits)

    @property
    def flags(self) -> ProviderFlags:
        return ProviderFlags(
            configured=not LiveSetting.objects.filter(name__startswith="TWILIO", error__isnull=False).exists(),
            test_sms=True,
            test_call=True,
            verification_call=True,
            verification_sms=True,
        )
