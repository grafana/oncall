from rest_framework.throttling import UserRateThrottle


class DemoWebhookThrottler(UserRateThrottle):
    scope = "test_webhook"
    rate = "30/m"
