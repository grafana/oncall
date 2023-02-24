from rest_framework.throttling import UserRateThrottle


class UserThrottle(UserRateThrottle):
    scope = "public_api"
    rate = "300/m"
