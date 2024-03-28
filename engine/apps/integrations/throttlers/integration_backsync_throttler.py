from rest_framework.throttling import SimpleRateThrottle


class BacksyncRateThrottle(SimpleRateThrottle):
    """
    Integration backsync rate limit
    """

    scope = "backsync"
    rate = "300/m"

    def get_cache_key(self, request, view):
        ident = request.auth.alert_receive_channel.pk
        return self.cache_format % {"scope": self.scope, "ident": ident}
