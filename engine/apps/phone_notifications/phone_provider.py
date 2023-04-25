from abc import ABC
from typing import Optional

from django.conf import settings
from django.utils.module_loading import import_string

from .exceptions import ProviderNotSupports
from .models import OnCallPhoneCall, OnCallSMS

# TODO: DOCUMENT ME! Document exceptions, classes, methods


class PhoneProvider(ABC):
    """
    PhoneProvider is an interface to all phone providers.
    It is needed to hide details of external phone providers from core code.
    """

    def make_notification_call(self, number: str, text: str, oncall_phone_call: OnCallPhoneCall):
        """
        make_notification_call makes a call to notify about alert group.

        make_notification_call is needed to be able to execute some logic only for notification calls,
        but not for test/verification/etc.
        For example receive status callback or react for number pressed.

        If your provider doesn't perform any additional logic in notifications just wrap make_call:

            def make_notification_call(self, number, text, oncall_phone_call):
                self.make_call(number, text)


        Args:
            number: phone number to call
            text: text of the call
            oncall_phone_call: instance of OnCallPhoneCall.
                You can use it to link provider phone call and oncall_phone_call (See TwilioPhoneProvider).

        Raises:
            FailedToMakeCall: if some exception in external provider happens
            ProviderNotSupports: if provider not supports calls (it's a valid use-case)
        """
        raise ProviderNotSupports

    def send_notification_sms(self, number: str, message: str, oncall_sms: OnCallSMS):
        """
        send_notification_sms sends a sms to notify about alert group

        send_notification_sms is needed to be able to execute some logic only for notification sms,
        but not for test/verification/etc. For example receive status callback (See TwilioPhoneProvider).
        You can just wrap send_sms if no additional logic is performed for notification sms:

            def send_notification_sms(self, number, text, oncall_phone_call):
                self.send_sms(number, text)

        Args:
            number: phone number to send sms
            text: text of the sms
            oncall_phone_call: instance of OnCallSMS.
                You can use it to link provider sms and oncall_sms (See TwilioPhoneProvider).


        Raises:
            FailedToSendSMS: if some exception in external provider happens
            ProviderNotSupports: if provider not supports calls (it's a valid use-case)
        """
        raise ProviderNotSupports

    def make_call(self, number: str, text: str):
        """
        make_call make a call with given text to given number.

        Args:
            number: phone number to make a call
            text: call text to deliver to user

        Raises:
            FailedToMakeCall: if some exception in external provider happens
            ProviderNotSupports: if provider not supports calls (it's a valid use-case)
        """
        raise ProviderNotSupports

    def send_sms(self, number: str, text: str):
        """
        send_sms sends an SMS to the specified phone number with the given text message.

        Args:
            number: phone number to send a sms
            text: text to deliver to user

        Raises:
            FailedToSendSMS: if some exception in external provider occurred
            ProviderNotSupports: if provider not supports calls

        """
        raise ProviderNotSupports

    def send_verification_sms(self, number: str):
        """
        send_verification_sms starts phone number verification by sending code via sms

        Args:
            number: number to verify

        Raises:
            FailedToStartVerification: if some exception in external provider occurred
            ProviderNotSupports: if concrete provider not phone number verification via sms
        """
        raise ProviderNotSupports

    def make_verification_call(self, number: str):
        """
        make_verification_call starts phone number verification by calling to user

        Args:
            number: number to verify

        Raises:
            FailedToStartVerification: if some exception in external provider occurred
            ProviderNotSupports: if concrete provider not phone number verification via call
        """
        raise ProviderNotSupports

    def finish_verification(self, number: str, code: str) -> Optional[str]:
        """
        finish_verification validates the verification code.

        Args:
             number: number to verify
             code: verification code
        Returns:
            verified phone number or None if code is invalid

        Raises:
            FailedToFinishVerification: when some exception in external service occurred
            ProviderNotSupports: if concrete provider not supports number verification
        """
        raise ProviderNotSupports


_provider = None

# TODO: phone_provider: store provider in global variable, or create instance each time to allow to modify it without restart of oncall
def get_phone_provider() -> PhoneProvider:
    # TODO: phone_provider: remove this, TwilioProvider hardcoded
    from ..twilioapp.phone_provider import TwilioPhoneProvider

    return TwilioPhoneProvider()
    global _provider
    if _provider is None:
        PhoneNotificatorClass = import_string(settings.PHONE_NOTIFICATOR)
        _provider = PhoneNotificatorClass()
    return _provider
