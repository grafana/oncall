import logging
import urllib.parse
from string import digits

from django.db.models import F, Q
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
from apps.twilioapp.models import (
    TwilioCallStatuses,
    TwilioPhoneCall,
    TwilioPhoneCallSender,
    TwilioSMS,
    TwilioSmsSender,
    TwilioVerificationSender,
)
from apps.twilioapp.status_callback import get_call_status_callback_url, get_sms_status_callback_url

logger = logging.getLogger(__name__)


class TwilioPhoneProvider(PhoneProvider):
    def make_notification_call(self, number: str, message: str) -> TwilioPhoneCall | None:
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
                logger.info("TwilioPhoneProvider.make_notification_call: error 21609, calling without callback_url")
                try_without_callback = True
            else:
                logger.error(f"TwilioPhoneProvider.make_notification_call: failed {e}")
                raise FailedToMakeCall(graceful_msg=self._get_graceful_msg(e, number))

        if try_without_callback:
            try:
                response = self._call_create(twiml_query, number, with_callback=False)
            except TwilioRestException as e:
                logger.error(f"TwilioPhoneProvider.make_notification_call: failed {e}")
                raise FailedToMakeCall(graceful_msg=self._get_graceful_msg(e, number))

        if response and response.status and response.sid:
            return TwilioPhoneCall(
                status=TwilioCallStatuses.DETERMINANT.get(response.status, None),
                sid=response.sid,
            )
        return None

    def send_notification_sms(self, number: str, message: str) -> TwilioSMS | None:
        try_without_callback = False
        response = None

        try:
            response = self._messages_create(number, message, with_callback=True)
        except TwilioRestException as e:
            # If status callback is not valid and not accessible from public url then trying to send message without it
            # https://www.twilio.com/docs/api/errors/21609
            if e.code == 21609:
                logger.info("TwilioPhoneProvider.send_notification_sms: error 21609, sending without callback_url")
                try_without_callback = True
            else:
                logger.error(f"TwilioPhoneProvider.send_notification_sms: failed {e}")
                raise FailedToSendSMS(graceful_msg=self._get_graceful_msg(e, number))

        if try_without_callback:
            try:
                response = self._messages_create(number, message, with_callback=False)
            except TwilioRestException as e:
                logger.error(f"TwilioPhoneProvider.send_notification_sms: failed {e}")
                raise FailedToSendSMS(graceful_msg=self._get_graceful_msg(e, number))

        if response and response.status and response.sid:
            return TwilioSMS(
                status=TwilioCallStatuses.DETERMINANT.get(response.status, None),
                sid=response.sid,
            )
        return None

    def send_verification_sms(self, number: str):
        self._send_verification_code(number, via="sms")

    def finish_verification(self, number: str, code: str):
        # I'm not sure if we need verification_and_parse via twilio pipeline here
        # Verification code anyway is sent to not verified phone number.
        # Just leaving it as it was before phone_provider refactoring.
        normalized_number, _ = self._normalize_phone_number(number)
        if normalized_number:
            try:
                client, verify_service_sid = self._verify_sender(number)
                verification_check = client.verify.services(verify_service_sid).verification_checks.create(
                    to=normalized_number, code=code
                )
                logger.info(f"TwilioPhoneProvider.finish_verification: verification_status {verification_check.status}")
                if verification_check.status == "approved":
                    return normalized_number
            except TwilioRestException as e:
                logger.error(f"TwilioPhoneProvider.finish_verification: failed to verify number {number}: {e}")
                raise FailedToFinishVerification(graceful_msg=self._get_graceful_msg(e, number))
        else:
            return None

    """
    Errors we will raise without graceful messages:

    20404 - We should not be requesting missing resources
    30808 - Unknown error, likely on the carrier side
    30007, 32017 - Blocked or filtered, Intermediary / Carrier Analytics blocked call
                due to poor reputation score on the telephone number:
        * We need to register our number or sender with the analytics provider or carrier for that jurisdiction
    """

    def _get_graceful_msg(self, e, number):
        if e.code in (30003, 30005):
            return f"Destination handset {number} is unreachable"
        elif e.code == 30004:
            return f"Sending message to {number} is blocked"
        elif e.code == 30006:
            return f"Cannot send to {number} is landline or unreachable carrier"
        elif e.code == 30410:
            return f"Provider for {number} is experiencing timeouts"
        elif e.code == 60200:
            return f"{number} is incorrectly formatted"
        elif e.code in (21215, 60410, 60605):
            return f"Verification to {number} is blocked"
        elif e.code == 60203:
            return f"Max verification attempts for {number} reached"
        return None

    def make_call(self, number: str, message: str):
        twiml_query = self._message_to_twiml(message, with_gather=False)
        try:
            self._call_create(twiml_query, number, with_callback=False)
        except TwilioRestException as e:
            logger.error(f"TwilioPhoneProvider.make_call: failed {e}")
            raise FailedToMakeCall(graceful_msg=self._get_graceful_msg(e, number))

    def send_sms(self, number: str, message: str):
        try:
            self._messages_create(number, message, with_callback=False)
        except TwilioRestException as e:
            logger.error(f"TwilioPhoneProvider.send_sms: failed {e}")
            raise FailedToSendSMS(graceful_msg=self._get_graceful_msg(e, number))

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
        client, from_ = self._phone_sender(to)
        url = "http://twimlets.com/echo?Twiml=" + twiml_query
        if with_callback:
            status_callback = get_call_status_callback_url()
            status_callback_events = ["initiated", "ringing", "answered", "completed"]
            return client.calls.create(
                url=url,
                to=to,
                from_=from_,
                method="GET",
                status_callback=status_callback,
                status_callback_event=status_callback_events,
                status_callback_method="POST",
            )
        else:
            return client.calls.create(
                url=url,
                to=to,
                from_=from_,
                method="GET",
            )

    def _messages_create(self, number: str, text: str, with_callback: bool):
        client, from_ = self._sms_sender(number)
        if with_callback:
            status_callback = get_sms_status_callback_url()
            return client.messages.create(body=text, to=number, from_=from_, status_callback=status_callback)
        else:
            return client.messages.create(
                body=text,
                to=number,
                from_=from_,
            )

    def _send_verification_code(self, number: str, via: str):
        # https://www.twilio.com/docs/verify/api/verification?code-sample=code-start-a-verification-with-sms&code-language=Python&code-sdk-version=6.x
        try:
            client, verify_service_sid = self._verify_sender(number)
            verification = client.verify.services(verify_service_sid).verifications.create(to=number, channel=via)
            logger.info(f"TwilioPhoneProvider._send_verification_code: verification status {verification.status}")
        except TwilioRestException as e:
            logger.error(f"Twilio verification start error: {e} to number {number}")
            raise FailedToStartVerification(graceful_msg=self._get_graceful_msg(e, number))

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
            response = self._default_twilio_api_client.lookups.phone_numbers(number).fetch()
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
    def _default_twilio_api_client(self):
        if live_settings.TWILIO_API_KEY_SID and live_settings.TWILIO_API_KEY_SECRET:
            return Client(
                live_settings.TWILIO_API_KEY_SID, live_settings.TWILIO_API_KEY_SECRET, live_settings.TWILIO_ACCOUNT_SID
            )
        else:
            return Client(live_settings.TWILIO_ACCOUNT_SID, live_settings.TWILIO_AUTH_TOKEN)

    @property
    def _default_twilio_number(self):
        return live_settings.TWILIO_NUMBER

    def _twilio_sender(self, sender_model, to):
        _, _, country_code = self._parse_number(to)
        sender = (
            sender_model.objects.filter(Q(country_code=country_code) | Q(country_code__isnull=True))
            .order_by(F("country_code").desc(nulls_last=True))
            .first()
        )

        if sender:
            return sender.account.get_twilio_api_client(), sender

        return self._default_twilio_api_client, None

    def _sms_sender(self, to):
        client, sender = self._twilio_sender(TwilioSmsSender, to)
        return client, sender.sender if sender else self._default_twilio_number

    def _phone_sender(self, to):
        client, sender = self._twilio_sender(TwilioPhoneCallSender, to)
        return client, sender.number if sender else self._default_twilio_number

    def _verify_sender(self, to):
        client, sender = self._twilio_sender(TwilioVerificationSender, to)
        return client, sender.verify_service_sid if sender else live_settings.TWILIO_VERIFY_SERVICE_SID

    def _get_calling_code(self, iso):
        for code, isos in COUNTRY_CODE_TO_REGION_CODE.items():
            if iso.upper() in isos:
                return code
        return None

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
            test_sms=False,
            test_call=True,
            verification_call=False,
            verification_sms=True,
        )
