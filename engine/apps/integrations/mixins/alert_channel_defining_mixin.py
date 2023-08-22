import logging
from time import perf_counter

from django.core import serializers
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db import OperationalError

from apps.user_management.exceptions import OrganizationMovedException

logger = logging.getLogger(__name__)


class AlertChannelDefiningMixin(object):
    """
    Mixin is defining "alert channel" used for this request, gathers Slack Team and Chanel to fulfill "request".
    To make it easy to access them in ViewSets.
    """

    CACHE_KEY_DB_FALLBACK = "cached_alert_receive_channels_db_fallback"  # Key for caching channels as a DB fallback
    CACHE_DB_FALLBACK_OBSOLETE_KEY = CACHE_KEY_DB_FALLBACK + "_obsolete_key"  # Used as a timer for re-caching
    CACHE_DB_FALLBACK_REFRESH_INTERVAL = 180

    CACHE_KEY_SHORT_TERM = "cached_alert_receive_channels_short_term"  # Key for caching channels to reduce DB load
    CACHE_SHORT_TERM_TIMEOUT = 5

    def dispatch(self, *args, **kwargs):
        from apps.alerts.models import AlertReceiveChannel

        logger.info("AlertChannelDefiningMixin started")
        start = perf_counter()
        alert_receive_channel = None
        try:
            # Trying to define from short-term cache
            cache_key_short_term = self.CACHE_KEY_SHORT_TERM + "_" + str(kwargs["alert_channel_key"])
            cached_alert_receive_channel_raw = cache.get(cache_key_short_term)
            if cached_alert_receive_channel_raw is not None:
                alert_receive_channel = next(serializers.deserialize("json", cached_alert_receive_channel_raw)).object

            if alert_receive_channel is None:
                # Trying to define channel from DB
                alert_receive_channel = AlertReceiveChannel.objects.get(token=kwargs["alert_channel_key"])
                # Update short term cache
                serialized = serializers.serialize("json", [alert_receive_channel])
                cache.set(cache_key_short_term, serialized, self.CACHE_SHORT_TERM_TIMEOUT)

                # Update cached channels
                if cache.get(self.CACHE_DB_FALLBACK_OBSOLETE_KEY) is None:
                    cache.set(self.CACHE_DB_FALLBACK_OBSOLETE_KEY, True, self.CACHE_DB_FALLBACK_REFRESH_INTERVAL)
                    self.update_alert_receive_channel_cache()

        except AlertReceiveChannel.DoesNotExist:
            raise PermissionDenied("Integration key was not found. Permission denied.")
        except OperationalError:
            logger.info("Cannot connect to database, using cache to consume alerts!")

            # Searching for a channel in a cache
            if cache.get(self.CACHE_KEY_DB_FALLBACK):
                for obj in serializers.deserialize("json", cache.get(self.CACHE_KEY_DB_FALLBACK)):
                    if obj.object.token == kwargs["alert_channel_key"]:
                        alert_receive_channel = obj.object

                if alert_receive_channel is None:
                    raise PermissionDenied("Integration key was not found in cache. Permission denied.")

            else:
                logger.info("Cache is empty!")
                raise
        else:
            if alert_receive_channel.organization.is_moved:
                raise OrganizationMovedException(alert_receive_channel.organization)
            if alert_receive_channel.organization.deleted_at:
                # It's better to raise OrganizarionDeletedException, but in legacy code PermissionDenied is returned when integration key not found.
                # So, keep it consistent.
                raise PermissionDenied("Integration key was not found. Permission denied.")

        del kwargs["alert_channel_key"]

        request = args[0]
        request.alert_receive_channel = alert_receive_channel
        finish = perf_counter()
        logger.info(f"AlertChannelDefiningMixin finished in {finish - start}")
        return super(AlertChannelDefiningMixin, self).dispatch(*args, **kwargs)

    def update_alert_receive_channel_cache(self):
        from apps.alerts.models import AlertReceiveChannel

        logger.info("Caching alert receive channels from database.")
        serialized = serializers.serialize("json", AlertReceiveChannel.objects.all())
        # Caching forever, re-caching is managed by "obsolete key"
        cache.set(self.CACHE_KEY_DB_FALLBACK, serialized, timeout=None)
