from rest_framework.throttling import UserRateThrottle
from ratelimit.utils import _split_rate
from django.conf import settings


class CustomRateUserThrottler(UserRateThrottle):
    """
    
    """
    def parse_rate(self, rate):
        "Use django ratelimit format to parse rate, i.e. '30/1m', instead of '30/m'"
        return _split_rate(rate)

    def allow_request(self, request, view):

        # Override default rate limit, if organization id is specified in CUSTOM_RATELIMITS 
        custom_ratelimits = settings.CUSTOM_RATELIMITS
        organization_id = str(request.user.organization_id)
        if organization_id in custom_ratelimits:
            self.rate = custom_ratelimits[organization_id]["public_api"]

        return super().allow_request(request, view)
    
class CustomRateOrganizationThrottler(CustomRateUserThrottler):

    def get_cache_key(self, request, view):

        if request.user.is_authenticated:
            ident = request.user.organization.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {"scope": self.scope, "ident": ident}
