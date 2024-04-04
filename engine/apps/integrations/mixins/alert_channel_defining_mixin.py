import logging
from time import perf_counter

from django.core import serializers
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db import OperationalError

from apps.user_management.exceptions import OrganizationMovedException

INTEGRATION_PERMISSION_DENIED_MESSAGE = "Integration key was not found. Permission denied."

CHANNEL_DOES_NOT_EXIST_PLACEHOLDER = "DOES_NOT_EXIST"

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
            if cached_alert_receive_channel_raw == CHANNEL_DOES_NOT_EXIST_PLACEHOLDER:
                logger.info(f"Integration {kwargs['alert_channel_key']} already cached as non-existent")
                raise PermissionDenied(INTEGRATION_PERMISSION_DENIED_MESSAGE)

            if cached_alert_receive_channel_raw is not None:
                try:
                    alert_receive_channel = next(
                        serializers.deserialize("json", cached_alert_receive_channel_raw)
                    ).object
                except serializers.base.DeserializationError:
                    # cached object model is outdated
                    alert_receive_channel = None

            if alert_receive_channel is None:
                # Trying to define channel from DB
                try:
                    alert_receive_channel = AlertReceiveChannel.objects_with_deleted.get(
                        token=kwargs["alert_channel_key"]
                    )
                except AlertReceiveChannel.DoesNotExist:
                    cache.set(cache_key_short_term, CHANNEL_DOES_NOT_EXIST_PLACEHOLDER, self.CACHE_SHORT_TERM_TIMEOUT)
                else:
                    # Update short term cache
                    serialized = serializers.serialize("json", [alert_receive_channel])
                    cache.set(cache_key_short_term, serialized, self.CACHE_SHORT_TERM_TIMEOUT)

                    # Update cached channels
                    if cache.get(self.CACHE_DB_FALLBACK_OBSOLETE_KEY) is None:
                        cache.set(self.CACHE_DB_FALLBACK_OBSOLETE_KEY, True, self.CACHE_DB_FALLBACK_REFRESH_INTERVAL)
                        self.update_alert_receive_channel_cache()
        except OperationalError:
            logger.info("Cannot connect to database, using cache to consume alerts!")

            # Searching for a channel in a cache
            if cache.get(self.CACHE_KEY_DB_FALLBACK):
                for obj in serializers.deserialize("json", cache.get(self.CACHE_KEY_DB_FALLBACK)):
                    if obj.object.token == kwargs["alert_channel_key"]:
                        alert_receive_channel = obj.object

                if alert_receive_channel is None:
                    logger.info(f"Integration {kwargs['alert_channel_key']} not found in fallback cache")
                    raise PermissionDenied(INTEGRATION_PERMISSION_DENIED_MESSAGE)

            else:
                logger.info("Cache is empty!")
                raise
        else:
            if not alert_receive_channel:
                logger.info(f"Integration {kwargs['alert_channel_key']} does not exist")
                raise PermissionDenied(INTEGRATION_PERMISSION_DENIED_MESSAGE)
            if alert_receive_channel.organization.is_moved:
                logger.info(
                    f"Channel {kwargs['alert_channel_key']} in organization {alert_receive_channel.organization.public_primary_key} is moved"
                )
                raise OrganizationMovedException(alert_receive_channel.organization)
            if alert_receive_channel.deleted_at or alert_receive_channel.organization.deleted_at:
                logger.info(
                    f"Channel {kwargs['alert_channel_key']} or organization {alert_receive_channel.organization.public_primary_key} is deleted"
                )
                raise PermissionDenied(INTEGRATION_PERMISSION_DENIED_MESSAGE)

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
