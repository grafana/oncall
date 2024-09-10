from rest_framework.throttling import UserRateThrottle
from django.conf import settings


class UserThrottle(UserRateThrottle):
    scope = "public_api"
    rate = "300/m"

    def __init__(self):

        # Override default rate limit, if organization id specified in CUSTOM_RATELIMITS 
        custom_ratelimits = settings.CUSTOM_RATELIMITS
        organization_id = str(self.request.alert_receive_channel.organization_id)
        if organization_id in custom_ratelimits:
            self.rate = custom_ratelimits[organization_id]["public_api"]
        super().__init__()
