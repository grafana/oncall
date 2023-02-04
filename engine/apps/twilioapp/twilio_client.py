import logging
import urllib.parse

from django.apps import apps
from django.urls import reverse
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from apps.base.utils import live_settings
from apps.twilioapp.constants import TEST_CALL_TEXT, TwilioLogRecordStatus, TwilioLogRecordType
from apps.twilioapp.utils import get_calling_code, get_gather_message, get_gather_url, parse_phone_number
from apps.twilioapp.phone_client import PhoneClient
from common.api_helpers.utils import create_engine_url

logger = logging.getLogger(__name__)


class TwilioClient(PhoneClient):
    @property
    def twilio_api_client(self):
        if live_settings.TWILIO_API_KEY_SID and live_settings.TWILIO_API_KEY_SECRET:
            return Client(
                live_settings.TWILIO_API_KEY_SID, live_settings.TWILIO_API_KEY_SECRET, live_settings.TWILIO_ACCOUNT_SID
            )
        else:
            return Client(live_settings.TWILIO_ACCOUNT_SID, live_settings.TWILIO_AUTH_TOKEN)

    @property
    def twilio_number(self):
        return live_settings.TWILIO_NUMBER

    def send_message(self, body, to):
        status_callback = create_engine_url(reverse("twilioapp:sms_status_events"))
        try:
            return self.twilio_api_client.messages.create(
                body=body, to=to, from_=self.twilio_number, status_callback=status_callback
            )
        except TwilioRestException as e:
            # If status callback is not valid and not accessible from public url then trying to send message without it
            # https://www.twilio.com/docs/api/errors/21609
            if e.code == 21609:
                logger.warning("twilio_client.send_message: Twilio error 21609. Status Callback is not public url")
                return self.twilio_api_client.messages.create(body=body, to=to, from_=self.twilio_number)
            raise e

    # Use responsibly
    def parse_number(self, number):
        try:
            response = self.twilio_api_client.lookups.phone_numbers(number).fetch()
            return True, response.phone_number, get_calling_code(response.country_code)
        except TwilioRestException as e:
            if e.code == 20404:
                print("Handled exception from twilio: " + str(e))
                return False, None, None
            if e.code == 20003:
                raise e
        except KeyError as e:
            print("Handled exception from twilio: " + str(e))
            return False, None, None

    def verification_start_via_twilio(self, user, phone_number, via):
        # https://www.twilio.com/docs/verify/api/verification?code-sample=code-start-a-verification-with-sms&code-language=Python&code-sdk-version=6.x
        verification = None
        try:
            verification = self.twilio_api_client.verify.services(
                live_settings.TWILIO_VERIFY_SERVICE_SID
            ).verifications.create(to=phone_number, channel=via)
        except TwilioRestException as e:
            logger.error(f"Twilio verification start error: {e} for User: {user.pk}")

            self.create_log_record(
                user=user,
                phone_number=(phone_number or ""),
                type=TwilioLogRecordType.VERIFICATION_START,
                status=TwilioLogRecordStatus.ERROR,
                succeed=False,
                error_message=str(e),
            )
        else:
            verification_status = verification.status
            logger.info(f"Verification status: {verification_status}")

            self.create_log_record(
                user=user,
                phone_number=phone_number,
                type=TwilioLogRecordType.VERIFICATION_START,
                payload=str(verification._properties),
                status=TwilioLogRecordStatus.DETERMINANT[verification_status],
                succeed=(verification_status != "denied"),
            )

        return verification

    def verification_check_via_twilio(self, user, phone_number, code):
        # https://www.twilio.com/docs/verify/api/verification-check?code-sample=code-check-a-verification-with-a-phone-number&code-language=Python&code-sdk-version=6.x
        succeed = False
        try:
            verification_check = self.twilio_api_client.verify.services(
                live_settings.TWILIO_VERIFY_SERVICE_SID
            ).verification_checks.create(to=phone_number, code=code)
        except TwilioRestException as e:
            logger.error(f"Twilio verification check error: {e} for User: {user.pk}")
            self.create_log_record(
                user=user,
                phone_number=(phone_number or ""),
                type=TwilioLogRecordType.VERIFICATION_CHECK,
                status=TwilioLogRecordStatus.ERROR,
                succeed=succeed,
                error_message=str(e),
            )
        else:
            verification_check_status = verification_check.status
            logger.info(f"Verification check status: {verification_check_status}")
            succeed = verification_check_status == "approved"

            self.create_log_record(
                user=user,
                phone_number=phone_number,
                type=TwilioLogRecordType.VERIFICATION_CHECK,
                payload=str(verification_check._properties),
                status=TwilioLogRecordStatus.DETERMINANT[verification_check_status],
                succeed=succeed,
            )

        return succeed

    def make_test_call(self, to):
        message = TEST_CALL_TEXT.format(
            channel_name="Test call",
            alert_group_name="Test notification",
            alerts_count=2,
        )
        self.make_call(message=message, to=to)

    def make_call(self, message, to, grafana_cloud=False):
        try:
            start_message = message.replace('"', "")

            gather_message = (
                (
                    f'<Gather numDigits="1" action="{get_gather_url()}" method="POST">'
                    f"<Say>{get_gather_message()}</Say>"
                    f"</Gather>"
                )
                if not grafana_cloud
                else ""
            )

            twiml_query = urllib.parse.quote(
                f"<Response><Say>{start_message}</Say>{gather_message}</Response>",
                safe="",
            )

            url = "http://twimlets.com/echo?Twiml=" + twiml_query
            status_callback = create_engine_url(reverse("twilioapp:call_status_events"))

            status_callback_events = ["initiated", "ringing", "answered", "completed"]

            return self.twilio_api_client.calls.create(
                url=url,
                to=to,
                from_=self.twilio_number,
                method="GET",
                status_callback=status_callback,
                status_callback_event=status_callback_events,
                status_callback_method="POST",
            )
        except TwilioRestException as e:
            # If status callback is not valid and not accessible from public url then trying to make call without it
            # https://www.twilio.com/docs/api/errors/21609
            if e.code == 21609:
                logger.warning("twilio_client.make_call: Twilio error 21609. Status Callback is not public url")
                return self.twilio_api_client.calls.create(
                    url=url,
                    to=to,
                    from_=self.twilio_number,
                    method="GET",
                )

            raise e

    def create_log_record(self, **kwargs):
        TwilioLogRecord = apps.get_model("twilioapp", "TwilioLogRecord")
        TwilioLogRecord.objects.create(**kwargs)

    def normalize_phone_number_via_twilio(self, phone_number):
        phone_number = parse_phone_number(phone_number)

        # Verify and parse phone number with Twilio API
        normalized_phone_number = None
        country_code = None
        if phone_number != "" and phone_number != "+":
            try:
                ok, normalized_phone_number, country_code = self.parse_number(phone_number)
                if normalized_phone_number == "":
                    normalized_phone_number = None
                    country_code = None
                if not ok:
                    normalized_phone_number = None
                    country_code = None
            except TypeError:
                return None, None

        return normalized_phone_number, country_code

    def notify_about_changed_verified_phone_number(self, text, phone_number):
        self.send_message(text, phone_number)


    def send_otp(self, user):
        res = self.verification_start_via_twilio(
            user=user, phone_number=user.unverified_phone_number, via="sms"
        )

        if res and res.status != "denied":
            return True
        else:
            logger.error(f"Failed to send verification code to User {user.pk}: \n{res}")
            return False
    

    def verify_otp(self, user, code):
        normalized_phone_number, _ = twilio_client.normalize_phone_number_via_twilio(user.unverified_phone_number)
        if normalized_phone_number:
            if normalized_phone_number == user.verified_phone_number:
                verified = False
                error = "This Phone Number has already been verified"
            elif self.verification_check_via_twilio(
                user=user,
                phone_number=normalized_phone_number,
                code=code
            ):
                old_verified_phone_number = user.verified_phone_number
                user.save_verified_phone_number(normalized_phone_number)
                # send sms to the new number and to the old one
                if old_verified_phone_number:
                    self.notify_about_changed_verified_phone_number(old_verified_phone_number)
                self.notify_about_changed_verified_phone_number(normalized_phone_number)

                verified = True
                error = None
            else:
                verified = False
                error = "Verification code is not correct."
        else:
            verified = False
            error = "Phone Number is incorrect"
            
        return verified, error

        
twilio_client = TwilioClient()
