import logging
from random import randint

from django.core.cache import cache

from .exceptions import FailedToSendSMS, FailedToStartVerification
from .phone_provider import PhoneProvider, ProviderFlags

logger = logging.getLogger(__name__)


class SimplePhoneProvider(PhoneProvider):
    """
    SimplePhoneProvider is an example of phone provider which supports only SMS messages.
    It is not intended for real-life usage and needed only as example of PhoneProviders suitable to use ONLY in OSS.
    """

    def send_notification_sms(self, number, message):
        self.send_sms(number, message)

    def send_sms(self, number, text):
        try:
            self._write_to_stdout(number, text)
        except Exception as e:
            # example of handling provider exceptions and converting them to exceptions from core OnCall code.
            logger.error(f"SimplePhoneProvider.send_sms: failed {e}")
            raise FailedToSendSMS

    def send_verification_sms(self, number):
        code = str(randint(100000, 999999))
        cache.set(self._cache_key(number), code, timeout=10 * 60)
        try:
            self._write_to_stdout(number, f"Your verification code is {code}")
        except Exception as e:
            # Example of handling provider exceptions and converting them to exceptions from core OnCall code.
            logger.error(f"SimplePhoneProvider.send_verification_sms: failed {e}")
            raise FailedToStartVerification

    def finish_verification(self, number, code):
        has = cache.get(self._cache_key(number))
        if has is not None and has == code:
            return number
        else:
            return None

    def _cache_key(self, number):
        return f"simple_provider_{number}"

    def _write_to_stdout(self, number, text):
        # print is just example of sending sms.
        # In real-life provider it will be some external api call.
        print(f'send message "{text}" to {number}')

    @property
    def flags(self) -> ProviderFlags:
        return ProviderFlags(
            configured=True,
            test_sms=True,
            test_call=False,
            verification_call=False,
            verification_sms=True,
        )
