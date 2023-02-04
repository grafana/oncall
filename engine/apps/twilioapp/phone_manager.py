import logging

from twilio.base.exceptions import TwilioRestException

from apps.twilioapp.twilio_client import twilio_client
from apps.twilioapp.asterisk_client import asterisk_client
from apps.twilioapp.phone_client import PhoneClient

from apps.base.utils import live_settings

logger = logging.getLogger(__name__)


class PhoneManager:
    def __init__(self, user):
        self.user = user
        self.phone_client = self.init_phone_client()

    def init_phone_client(self) -> PhoneClient:
        if live_settings.PHONE_PROVIDER == "Asterisk":
            return asterisk_client
        elif live_settings.PHONE_PROVIDER == "Twilio":
            return twilio_client
        else:
            logger.exception(f"Invalid phone provider {live_settings.PHONE_PROVIDER}")

    def send_verification_code(self):
        if self.user.unverified_phone_number == self.user.verified_phone_number:
            return False
        else:
            if self.phone_client.send_otp(self.user):
                return True
            else:
                logger.error(f"Failed to send verification code to User {self.user.pk}")

    def verify_phone_number(self, code):
        verified, error = self.phone_client.verify_otp(self.user, code)
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
            self.phone_client.send_message(text, phone_number)
        except Exception as e:
            logger.error(
                f"Failed to notify user {self.user.pk} about phone number "
                f"{'connection' if connected else 'disconnection'}:\n{e}"
            )
