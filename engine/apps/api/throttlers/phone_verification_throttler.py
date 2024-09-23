from common.api_helpers.custom_rate_scoped_throttler import CustomRateOrganizationThrottler, CustomRateUserThrottler


class GetPhoneVerificationCodeThrottlerPerUser(CustomRateUserThrottler):
    rate = "5/10m"
    scope = "get_phone_verification_code_per_user"


class VerifyPhoneNumberThrottlerPerUser(CustomRateUserThrottler):
    rate = "50/10m"
    scope = "verify_phone_number_per_user"


class GetPhoneVerificationCodeThrottlerPerOrg(CustomRateOrganizationThrottler):
    rate = "50/10m"
    scope = "get_phone_verification_code_per_org"


class VerifyPhoneNumberThrottlerPerOrg(CustomRateOrganizationThrottler):
    rate = "50/10m"
    scope = "verify_phone_number_per_org"
