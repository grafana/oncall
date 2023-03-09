from common.api_helpers.custom_rate_scoped_throttler import CustomRateScopedThrottler


class GetPhoneVerificationCodeThrottlerPerUser(CustomRateScopedThrottler):
    def get_scope(self):
        return "get_phone_verification_code_per_user"

    def get_throttle_limits(self):
        return 5, 10 * 60


class VerifyPhoneNumberThrottlerPerUser(CustomRateScopedThrottler):
    def get_scope(self):
        return "verify_phone_number_per_user"

    def get_throttle_limits(self):
        return 50, 10 * 60


class GetPhoneVerificationCodeThrottlerPerOrg(CustomRateScopedThrottler):
    def get_scope(self):
        return "get_phone_verification_code_per_org"

    def get_throttle_limits(self):
        return 50, 10 * 60

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.organization.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {"scope": self.scope, "ident": ident}


class VerifyPhoneNumberThrottlerPerOrg(CustomRateScopedThrottler):
    def get_scope(self):
        return "verify_phone_number_per_org"

    def get_throttle_limits(self):
        return 50, 10 * 60

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.organization.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {"scope": self.scope, "ident": ident}
