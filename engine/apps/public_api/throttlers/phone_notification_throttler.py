from rest_framework.throttling import UserRateThrottle


class PhoneNotificationThrottler(UserRateThrottle):
    scope = "phone_notification"
    rate = "60/m"
