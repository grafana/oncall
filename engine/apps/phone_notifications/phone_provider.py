import typing
from abc import ABC, abstractmethod
from dataclasses import dataclass

from django.conf import settings
from django.utils.module_loading import import_string

from apps.base.utils import live_settings
from apps.phone_notifications.exceptions import ProviderNotSupports
from apps.phone_notifications.models import ProviderPhoneCall, ProviderSMS


@dataclass
class ProviderFlags:
    """
    ProviderFlags is set of feature flags enabled for concrete provider.
    It is needed to show correct buttons in UI.

    Attributes:
       configured: Indicates if provider LiveSettings are valid. If LiveSettings cannot be validated, return True.
       test_sms: Indicates if provider allows to send test_sms
       test_call: Indicates if provider allows to make test_call
       verification_call: Indicates if provider allows to validate number via call
       verification_sms: Indicates if provider allows to validate number via sms
    """

    configured: bool
    test_sms: bool
    test_call: bool
    verification_call: bool
    verification_sms: bool


class PhoneProvider(ABC):
    """
    PhoneProvider is an interface to all phone providers.
    It is needed to hide details of external phone providers from core code.

    To implement custom phone provider:
        1. Implement your ConcretePhoneProvider inherited from PhoneProvider.
        2. Add needed env variables to django settings and to LiveSettings.
        3. Add your PhoneProvider to settings.PHONE_PROVIDERS dict.

    For reference, you can check:
        SimplePhoneProvider as example of tiny, but working provider.
        TwilioPhoneProvider as example of complicated phone provider which supports status callbacks and gather actions.
    """

    def make_notification_call(self, number: str, text: str) -> typing.Optional[ProviderPhoneCall]:
        """
        make_notification_call makes a call to notify about alert group and optionally returns unsaved ProviderPhoneCall
        instance. If returned, instance will be linked to PhoneCallRecord and saved by PhoneBackend.
        Check ProviderPhoneCall doc for more info.

        If provider doesn't perform additional logic for notifications or doesn't save phone call data - wrap make_call:
            def make_notification_call(self, number, text):
                self.make_call(number, text)

        Args:
            number: phone number to call
            text: text of the call
        Returns:
            Unsaved ProviderPhoneCall instance to link to PhoneCallRecord or None if provider-specific data not stored.

        Raises:
            FailedToMakeCall: if some exception in external provider happens.
            ProviderNotSupports: if provider not supports calls (it's a valid use-case).
        """
        raise ProviderNotSupports

    def send_notification_sms(self, number: str, message: str) -> typing.Optional[ProviderSMS]:
        """
        send_notification_sms sends a sms to notify about alert group.

        send_notification_sms sends a sms to notify about alert group and optionally returns unsaved ProviderSMS
        instance. If returned, instance will be linked to SMSRecord and saved by PhoneBackend.

        You can just wrap send_sms if no additional logic is performed for notification sms:

            def send_notification_sms(self, number, text, phone_call_record):
                self.send_sms(number, text)

        Args:
            number: phone number to send sms
            message: text of the sms
        Returns:
            Unsaved ProviderSMS instance to link to SMSRecord or None if provider-specific data not stored.

        Raises:
            FailedToSendSMS: if some exception in external provider happens
            ProviderNotSupports: if provider not supports sms (it's a valid use-case)
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
        send_sms sends an SMS to the specified phone number with the given text.

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

    def finish_verification(self, number: str, code: str) -> typing.Optional[str]:
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

    @property
    @abstractmethod
    def flags(self) -> ProviderFlags:
        """
        flags returns ProviderFlags instance to control web UI
        """
        raise NotImplementedError


_providers: typing.Dict[str, PhoneProvider] = {}


def get_phone_provider() -> PhoneProvider:
    global _providers
    # load all providers in memory on first call
    if len(_providers) == 0:
        for provider_alias, importpath in settings.PHONE_PROVIDERS.items():
            _providers[provider_alias] = import_string(importpath)()

    if live_settings.PHONE_PROVIDER not in settings.PHONE_PROVIDERS.keys():
        return _providers[settings.DEFAULT_PHONE_PROVIDER]

    return _providers[live_settings.PHONE_PROVIDER]
