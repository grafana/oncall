from rest_framework.throttling import UserRateThrottle


class UserThrottle(UserRateThrottle):
    """
    __init__ and allow_request are overridden because we want rate 300/5m,
    but default rate parser implementation doesn't allow to specify length of period (only m, d, etc.)
    (See SimpleRateThrottle.parse_rate)

    """

    def __init__(self):
        self.num_requests, self.duration = self.get_throttle_limits()

    def get_throttle_limits(self):
        """
        This method exits for speed up tests.
        :return tuple requests/seconds
        """
        return 300, 60

    def allow_request(self, request, view):
        """
        Implement the check to see if the request should be throttled.

        On success calls `throttle_success`.
        On failure calls `throttle_failure`.
        """

        self.key = self.get_cache_key(request, view)
        if self.key is None:
            return True

        self.history = self.cache.get(self.key, [])
        self.now = self.timer()

        # Drop any requests from the history which have now passed the
        # throttle duration
        while self.history and self.history[-1] <= self.now - self.duration:
            self.history.pop()
        if len(self.history) >= self.num_requests:
            return self.throttle_failure()
        return self.throttle_success()
