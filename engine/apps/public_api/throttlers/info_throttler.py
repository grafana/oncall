from common.api_helpers.custom_rate_scoped_throttler import CustomRateUserThrottler


class InfoThrottler(CustomRateUserThrottler):
    scope = "info"
    rate = "100/m"
