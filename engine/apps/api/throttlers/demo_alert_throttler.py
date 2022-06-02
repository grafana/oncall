from rest_framework.throttling import UserRateThrottle


class DemoAlertThrottler(UserRateThrottle):
    scope = "send_demo_alert"
    rate = "30/m"
