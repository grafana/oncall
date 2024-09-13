from common.api_helpers.custom_rate_scoped_throttler import CustomRateUserThrottler


class PhoneNotificationThrottler(CustomRateUserThrottler):
    scope = "phone_notification"
    rate = "60/m"
