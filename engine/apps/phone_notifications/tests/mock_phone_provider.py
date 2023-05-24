from apps.phone_notifications.phone_provider import PhoneProvider, ProviderFlags


class MockPhoneProvider(PhoneProvider):
    """
    MockPhoneProvider exists only for tests, feel free to mock any method to imitate any use-case, exception, etc.
    """

    def make_notification_call(self, number: str, text: str):
        pass

    def send_notification_sms(self, number: str, message: str):
        pass

    def make_call(self, number: str, text: str):
        pass

    def send_sms(self, number: str, text: str):
        pass

    def send_verification_sms(self, number: str):
        pass

    def make_verification_call(self, number: str):
        pass

    def finish_verification(self, number: str, code: str):
        pass

    @property
    def flags(self) -> ProviderFlags:
        return ProviderFlags(
            configured=True,
            test_sms=True,
            test_call=True,
            verification_call=True,
            verification_sms=True,
        )
