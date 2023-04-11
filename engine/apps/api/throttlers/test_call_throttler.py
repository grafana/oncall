from rest_framework.throttling import UserRateThrottle


class TestCallThrottler(UserRateThrottle):
    scope = "make_test_call"
    rate = "5/m"
