from common.api_helpers.custom_rate_scoped_throttler import CustomRateUserThrottler


class DemoAlertThrottler(CustomRateUserThrottler):
    scope = "send_demo_alert"
    rate = "30/m"
