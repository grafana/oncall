from random import randint

from django.core.cache import cache

from .phone_provider import PhoneProvider


class SimplePhoneProvider(PhoneProvider):
    """
    SimplePhoneProvider is an example of phone provider which supports only SMS messages.
    It is not intended for real-life usage and needed only as example of PhoneProviders suitable to use ONLY in OSS.
    """

    def send_notification_sms(self, number, message, oncall_sms):
        self.send_sms(number, message)

    def send_sms(self, number, text):
        print(f'SimplePhoneProvider.send_sms: send message "{text}" to {number}')

    def send_verification_sms(self, number):
        code = str(randint(100000, 999999))
        cache.set(self._cache_key(number), code, timeout=10 * 60)
        self.send_sms(number, f"Your verification code is {code}")

    def finish_verification(self, number, code):
        has = cache.get(self._cache_key(number))
        if has is not None and has == code:
            return number
        else:
            return None

    def _cache_key(self, number):
        return f"simple_provider_{number}"
