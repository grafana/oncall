from common.api_helpers.custom_rate_scoped_throttler import CustomRateScopedThrottler


class GetPhoneVerificationCodeThrottler(CustomRateScopedThrottler):
    def get_scope(self):
        return "get_phone_verification_code"

    def get_throttle_limits(self):
        return 5, 10 * 60


class VerifyPhoneNumberThrottler(CustomRateScopedThrottler):
    def get_scope(self):
        return "verify_phone_number"

    def get_throttle_limits(self):
        return 5, 10 * 60
