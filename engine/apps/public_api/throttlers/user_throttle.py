from common.api_helpers.custom_rate_scoped_throttler import CustomRateUserThrottler


class UserThrottle(CustomRateUserThrottler):
    scope = "public_api"
    rate = "300/m"
