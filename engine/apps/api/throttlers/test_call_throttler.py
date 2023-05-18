from rest_framework.throttling import UserRateThrottle


class TestCallThrottler(UserRateThrottle):
    scope = "make_test_call"
    rate = "5/m"


class TestPushThrottler(UserRateThrottle):
    scope = "send_test_push"
    rate = "5/m"
