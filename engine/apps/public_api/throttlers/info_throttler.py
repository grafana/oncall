from rest_framework.throttling import UserRateThrottle


class InfoThrottler(UserRateThrottle):
    scope = "info"
    rate = "100/m"
