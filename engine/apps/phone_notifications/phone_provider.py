from abc import ABC, abstractmethod

from django.conf import settings
from django.utils.module_loading import import_string

from .exceptions import ProviderNotSupports
from .models import OnCallPhoneCall, OnCallSMS

# TODO: DOCUMENT ME! Document exceptions, classes, methods


class PhoneProvider(ABC):
    """
    PhoneProvider is an interface to all phone providers.
    It is needed to hide details of external phone providers from core code.

    If you are implementing custom phone provider consider to read doc
    TODO: phone_notificator: doc
    """

    def make_notification_call(self, number: str, text: str, oncall_phone_call: OnCallPhoneCall):
        """
        make_notification_call makes a call to notify user about alert group.

        Parameters:
            number: phone number to call
            text: text of the call
            oncall_phone_call: instance of OnCallPhoneCall
                It's needed to link call from external provider to call in oncall.
                Usually it is needed to support callbacks from external provider

        Raises:
            FailedToMakeCall: if some exception in external provider happens
            ProviderNotSupports: if provider not supports calls (it's a valid use-case)
        """
        raise ProviderNotSupports

    def send_notification_sms(self, number: str, message: str, oncall_sms: OnCallSMS):
        """
        send_notification_sms sends a sms to notify user about alert group
        """
        raise ProviderNotSupports

    def make_call(self, number: str, text: str):
        """
        make_call make a call with given text to given number.

        Parameters:
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

        Parameters:
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

        Parameters:
            number: number to verify

        Raises:
            FailedToStartVerification: if some exception in external provider occurred
            ProviderNotSupports: if concrete provider not phone number verification via sms
        """
        raise ProviderNotSupports

    def make_verification_call(self, number: str):
        """
        make_verification_call starts phone number verification by calling to user

        Parameters:
            number: number to verify

        Raises:
            FailedToStartVerification: if some exception in external provider occurred
            ProviderNotSupports: if concrete provider not phone number verification via call
        """
        raise ProviderNotSupports

    def finish_verification(self, number: str, code: str):
        """
        finish_verification validates the verification code

        Parameters:
             number: number to verify
             code: veritication code

        Raises:
            FailedToFinishVerification, when some exception in external service occurred
            ProviderNotSupports, if concrete provider not supports number verification
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
