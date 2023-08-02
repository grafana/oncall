import logging
from abc import ABC, abstractmethod
from functools import wraps

from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.views import View
from ratelimit import ALL
from ratelimit.exceptions import Ratelimited
from ratelimit.utils import is_ratelimited

from apps.integrations.tasks import start_notify_about_integration_ratelimit

logger = logging.getLogger(__name__)


RATELIMIT_INTEGRATION = 300
RATELIMIT_TEAM = 900
RATELIMIT_REASON_INTEGRATION = "channel"
RATELIMIT_REASON_TEAM = "team"


def get_rate_limit_per_channel_key(_, request):
    """
    Rate limiting based on AlertReceiveChannel's PK
    """
    return str(request.alert_receive_channel.pk)


def get_rate_limit_per_team_key(_, request):
    """
    Rate limiting based on AlertReceiveChannel's team PK
    """
    return str(request.alert_receive_channel.organization_id)


def ratelimit(group=None, key=None, rate=None, method=ALL, block=False, reason=None):
    """
    This decorator is an updated version of:
        from ratelimit.decorators import ratelimit

    Because we need to store ratelimit reason.
    """

    def decorator(fn):
        @wraps(fn)
        def _wrapped(*args, **kw):
            # Work as a CBV method decorator.
            if isinstance(args[0], HttpRequest):
                request = args[0]
            else:
                request = args[1]

            request.limited = getattr(request, "limited", False)
            was_limited_before = request.limited

            ratelimited = is_ratelimited(
                request=request, group=group, fn=fn, key=key, rate=rate, method=method, increment=True
            )

            # We need to know if it's the first ratelimited request for notification purposes.
            request.is_first_rate_limited_request = getattr(request, "is_first_rate_limited_request", False)
            request.ratelimit_reason = getattr(request, "ratelimit_reason", None)
            request.ratelimit_reason_key = getattr(request, "ratelimit_reason_key", None)

            # This decorator could be executed multiple times per request.
            # Making sure we don't overwrite this flag.
            if not request.is_first_rate_limited_request:
                request.is_first_rate_limited_request = request.limited and not was_limited_before

                # Saving reason only for the first ratelimit occurrence to avoid overwriting.
                if request.is_first_rate_limited_request:
                    request.ratelimit_reason = reason
                    request.ratelimit_reason_key = None
                    if key is not None:
                        request.ratelimit_reason_key = key(None, request)

            if ratelimited and block:
                raise Ratelimited()
            return fn(*args, **kw)

        return _wrapped

    return decorator


def is_ratelimit_ignored(alert_receive_channel):
    from apps.base.models import DynamicSetting

    integration_token_to_ignore_ratelimit = DynamicSetting.objects.get_or_create(
        name="integration_tokens_to_ignore_ratelimit",
        defaults={
            "json_value": [
                "dummytoken_uniq_1213kj1h3",
            ]
        },
    )[0]
    return alert_receive_channel.token in integration_token_to_ignore_ratelimit.json_value


class RateLimitMixin(ABC, View):
    def dispatch(self, *args, **kwargs):
        if self.request.method in self.methods_to_limit:
            self.execute_rate_limit_with_notification_logic()

            if self.request.limited:
                try:
                    if not is_ratelimit_ignored(self.request.alert_receive_channel):
                        return self.get_ratelimit_http_response()
                    else:
                        logger.info(f"Token {self.request.alert_receive_channel.token} saved from the ratelimit!")
                except Exception as e:
                    logger.info(f"Exception in the ratelimit avoidance mechanism! {e}")
                    return self.get_ratelimit_http_response()

        return super().dispatch(*args, **kwargs)

    def get_ratelimit_http_response(self):
        return HttpResponse(self.ratelimit_text, status=429)

    @property
    @abstractmethod
    def ratelimit_text(self):
        raise NotImplementedError

    def execute_rate_limit_with_notification_logic(self, *args, **kwargs):
        self.execute_rate_limit(self.request)
        self.notify()

    @property
    @abstractmethod
    def methods_to_limit(self):
        raise NotImplementedError

    @abstractmethod
    def notify(self):
        raise NotImplementedError

    @abstractmethod
    def execute_rate_limit(self, request):
        raise NotImplementedError


class IntegrationHeartBeatRateLimitMixin(RateLimitMixin, View):
    TEXT_INTEGRATION_HEARTBEAT = """
    We received too many heartbeats from integration and had to apply rate limiting.
    Please don't hesitate to reach out in case you need increased capacity."
    """

    def notify(self):
        """
        It is don't needed to notify about heartbeat limits now
        """
        pass

    @ratelimit(
        key=get_rate_limit_per_channel_key,
        rate=str(RATELIMIT_INTEGRATION) + "/5m",
        group="integration",
        reason=RATELIMIT_REASON_INTEGRATION,
    )
    @ratelimit(
        key=get_rate_limit_per_team_key, rate=str(RATELIMIT_TEAM) + "/5m", group="team", reason=RATELIMIT_REASON_TEAM
    )
    def execute_rate_limit(self, *args, **kwargs):
        pass

    @property
    def ratelimit_text(self):
        return self.TEXT_INTEGRATION_HEARTBEAT

    @property
    def methods_to_limit(self):
        return {"GET", "POST"}


class IntegrationRateLimitMixin(RateLimitMixin, View):
    TEXT_INTEGRATION = (
        "Rate-limiting has been applied to your account "
        "because too many alerts were sent from your {integration} integration. "
        "Rate-limiting is activated so you will continue to receive alerts from other integrations. "
        "Read more about rate limits in our docs. "
        "To increase your capacity, reach out to our support team."
    )

    TEXT_WORKSPACE = (
        "Rate-limiting has been applied to your account "
        "because too many alerts were sent from multiple integrations. "
        "Read more about rate limits in our docs. "
        "To increase your capacity, reach out to our support team."
    )

    @ratelimit(
        key=get_rate_limit_per_channel_key,
        rate=str(RATELIMIT_INTEGRATION) + "/5m",
        group="integration",
        reason=RATELIMIT_REASON_INTEGRATION,
    )
    @ratelimit(
        key=get_rate_limit_per_team_key, rate=str(RATELIMIT_TEAM) + "/5m", group="team", reason=RATELIMIT_REASON_TEAM
    )
    def execute_rate_limit(self, *args, **kwargs):
        pass

    def notify(self):
        if self.request.limited and self.request.is_first_rate_limited_request:
            team_id = self.request.alert_receive_channel.organization_id

            # TODO: post to the other destinations too.

            cache_key = "rate_limit_notification_sent_team_" + str(team_id)

            if cache.get(cache_key) is None:
                start_notify_about_integration_ratelimit.apply_async((team_id, self.ratelimit_text), expires=60 * 5)
                cache.set(cache_key, True, 60 * 15)
                logging.debug(f"Setting rate limit notification no-spam key: {cache_key}")

    @property
    def ratelimit_text(self):
        if self.request.ratelimit_reason == RATELIMIT_REASON_INTEGRATION:
            return self.TEXT_INTEGRATION.format(
                integration=self.request.alert_receive_channel.verbal_name,
            )
        else:
            return self.TEXT_WORKSPACE

    @property
    def methods_to_limit(self):
        return {"POST"}
