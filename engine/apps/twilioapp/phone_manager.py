import logging

from twilio.base.exceptions import TwilioRestException

from apps.twilioapp.twilio_client import twilio_client
from apps.twilioapp.asterisk_client import asterisk_client

from apps.base.utils import live_settings

logger = logging.getLogger(__name__)


class PhoneManager:
    def __init__(self, user):
        self.user = user

    def send_verification_code(self):
        if live_settings.PHONE_PROVIDER == "Asterisk":
            otp, hearable_otp = asterisk_client.generate_otp()
            self.user.asterisk_otp = otp
            self.user.save()

            asterisk_client.make_call(f"Your OTP code is {hearable_otp}. " * 2, self.user.unverified_phone_number)
            return True
        else:
            if self.user.unverified_phone_number != self.user.verified_phone_number:
                res = twilio_client.verification_start_via_twilio(
                    user=self.user, phone_number=self.user.unverified_phone_number, via="sms"
                )
                if res and res.status != "denied":
                    return True
                else:
                    logger.error(f"Failed to send verification code to User {self.user.pk}:\n{res}")
            return False

    def verify_phone_number(self, code):
        if live_settings.PHONE_PROVIDER == "Asterisk":
            if self.user.unverified_phone_number == self.user.verified_phone_number:
                verified = False
                error = "This Phone Number has already been verified"
            elif self.user.asterisk_otp == code:
                self.user.save_verified_phone_number(self.user.unverified_phone_number)
                verified = True
                error = None
            else:
                verified = False
                error = "Verification code is not correct"
        else:
            normalized_phone_number, _ = twilio_client.normalize_phone_number_via_twilio(self.user.unverified_phone_number)
            if normalized_phone_number:
                if normalized_phone_number == self.user.verified_phone_number:
                    verified = False
                    error = "This Phone Number has already been verified."
                elif twilio_client.verification_check_via_twilio(
                    user=self.user,
                    phone_number=normalized_phone_number,
                    code=code,
                ):
                    old_verified_phone_number = self.user.verified_phone_number
                    self.user.save_verified_phone_number(normalized_phone_number)
                    # send sms to the new number and to the old one
                    if old_verified_phone_number:
                        # notify about disconnect
                        self.notify_about_changed_verified_phone_number(old_verified_phone_number)
                    # notify about new connection
                    self.notify_about_changed_verified_phone_number(normalized_phone_number, True)

                    verified = True
                    error = None
                else:
                    verified = False
                    error = "Verification code is not correct."
            else:
                verified = False
                error = "Phone Number is incorrect."
        return verified, error

    def forget_phone_number(self):
        if self.user.verified_phone_number or self.user.unverified_phone_number:
            old_verified_phone_number = self.user.verified_phone_number
            self.user.clear_phone_numbers()
            if old_verified_phone_number:
                self.notify_about_changed_verified_phone_number(old_verified_phone_number)
            return True
        return False

    def notify_about_changed_verified_phone_number(self, phone_number, connected=False):
        text = (
            f"This phone number has been {'connected to' if connected else 'disconnected from'} Grafana OnCall team "
            f'"{self.user.organization.stack_slug}"\nYour Grafana OnCall <3'
        )
        try:
            twilio_client.send_message(text, phone_number)
        except TwilioRestException as e:
            logger.error(
                f"Failed to notify user {self.user.pk} about phone number "
                f"{'connection' if connected else 'disconnection'}:\n{e}"
            )
