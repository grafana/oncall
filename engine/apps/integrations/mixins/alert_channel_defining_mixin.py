import logging
from time import perf_counter

from django.core import serializers
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db import OperationalError

from apps.user_management.exceptions import OrganizationMovedException

INTEGRATION_PERMISSION_DENIED_MESSAGE = "Integration key was not found. Permission denied."

CHANNEL_DOES_NOT_EXIST_PLACEHOLDER = "DOES_NOT_EXIST"
CHANNEL_MOVED_PLACEHOLDER = "MOVED"

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
        token = str(kwargs["alert_channel_key"])
        logger.info(f"AlertChannelDefiningMixin started token={token}")
        start = perf_counter()
        alert_receive_channel, status = self.get_alert_receive_channel_from_cache(token)

        if status == CHANNEL_MOVED_PLACEHOLDER:
            self.handle_organization_moved(token)

        if not alert_receive_channel or status == CHANNEL_DOES_NOT_EXIST_PLACEHOLDER:
            logger.info(f"Integration {token} does not exist")
            raise PermissionDenied(INTEGRATION_PERMISSION_DENIED_MESSAGE)

        del kwargs["alert_channel_key"]
        request = args[0]
        request.alert_receive_channel = alert_receive_channel
        finish = perf_counter()
        logger.info(f"AlertChannelDefiningMixin finished in {finish - start}")
        return super(AlertChannelDefiningMixin, self).dispatch(*args, **kwargs)

    def get_alert_receive_channel_from_cache(self, token):
        # Trying to define from short-term cache
        cache_key_short_term = self.CACHE_KEY_SHORT_TERM + "_" + token
        cached_alert_receive_channel_raw = cache.get(cache_key_short_term)

        if cached_alert_receive_channel_raw == CHANNEL_DOES_NOT_EXIST_PLACEHOLDER:
            return None, CHANNEL_DOES_NOT_EXIST_PLACEHOLDER

        if cached_alert_receive_channel_raw == CHANNEL_MOVED_PLACEHOLDER:
            return None, CHANNEL_MOVED_PLACEHOLDER

        if not cached_alert_receive_channel_raw:
            try:
                alert_receive_channel = next(serializers.deserialize("json", cached_alert_receive_channel_raw)).object
                return alert_receive_channel, None
            except serializers.base.DeserializationError:
                # cached object model is outdated
                pass

        alert_receive_channel, db_ok = self.get_alert_receive_channel_from_db(token)
        if not alert_receive_channel:
            logger.info(f"Channel {token} does not exist")
            cache.set(cache_key_short_term, CHANNEL_DOES_NOT_EXIST_PLACEHOLDER, self.CACHE_SHORT_TERM_TIMEOUT)
            return None, CHANNEL_DOES_NOT_EXIST_PLACEHOLDER

        if db_ok:
            if alert_receive_channel.organization.is_moved:
                logger.info(
                    f"Channel {token} organization {alert_receive_channel.organization.public_primary_key} is moved"
                )
                cache_key_organization_short_term = self.CACHE_KEY_ORGANIZATION_SHORT_TERM + "_" + token
                serialized_organization = serializers.serialize("json", [alert_receive_channel.organization])
                cache.set(cache_key_organization_short_term, serialized_organization, self.CACHE_SHORT_TERM_TIMEOUT)
                return None, CHANNEL_MOVED_PLACEHOLDER
            if alert_receive_channel.organization.deleted_at:
                # Needs to be checked after is_moved since is_deleted is set for moved orgs
                logger.info(
                    f"Channel {token} organization {alert_receive_channel.organization.public_primary_key} is deleted"
                )
                cache.set(cache_key_short_term, CHANNEL_DOES_NOT_EXIST_PLACEHOLDER, self.CACHE_SHORT_TERM_TIMEOUT)
                return None, CHANNEL_DOES_NOT_EXIST_PLACEHOLDER

            # Update short term cache
            serialized = serializers.serialize("json", [alert_receive_channel])
            cache.set(cache_key_short_term, serialized, self.CACHE_SHORT_TERM_TIMEOUT)

            # Update cached channels
            if cache.get(self.CACHE_DB_FALLBACK_OBSOLETE_KEY) is None:
                cache.set(self.CACHE_DB_FALLBACK_OBSOLETE_KEY, True, self.CACHE_DB_FALLBACK_REFRESH_INTERVAL)
                self.update_alert_receive_channel_cache()

        return alert_receive_channel, None

    def get_alert_receive_channel_from_db(self, token):
        from apps.alerts.models import AlertReceiveChannel

        try:
            alert_receive_channel = AlertReceiveChannel.objects.get(token=token)
            return alert_receive_channel, True
        except AlertReceiveChannel.DoesNotExist:
            return None, True
        except OperationalError:
            logger.info("Cannot connect to database, using cache to consume alerts!")
            return self.get_alert_receive_channel_from_db_fallback(token), False

    def get_alert_receive_channel_from_db_fallback(self, token):
        if cache.get(self.CACHE_KEY_DB_FALLBACK):
            for obj in serializers.deserialize("json", cache.get(self.CACHE_KEY_DB_FALLBACK)):
                if obj.object.token == token:
                    return obj.object
        else:
            logger.info("Cache is empty!")
            raise
        logger.info(f"Integration {token} not found in fallback cache")
        return None

    def update_alert_receive_channel_cache(self):
        from apps.alerts.models import AlertReceiveChannel

        logger.info("Caching alert receive channels from database.")
        serialized = serializers.serialize("json", AlertReceiveChannel.objects.all())
        # Caching forever, re-caching is managed by "obsolete key"
        cache.set(self.CACHE_KEY_DB_FALLBACK, serialized, timeout=None)

    def handle_organization_moved(self, token):
        # Organization lookup still occurs here, can be optimized if common enough
        from apps.alerts.models import AlertReceiveChannel

        try:
            alert_receive_channel = AlertReceiveChannel.objects.get(token=token)
        except AlertReceiveChannel.DoesNotExist:
            logger.info(f"Previously moved alert receive channel token={token} not found")
            raise PermissionDenied(INTEGRATION_PERMISSION_DENIED_MESSAGE)
        except OperationalError:
            logger.info(
                f"Moved organization for alert receive channel token={token} is not compatible with DB fallback"
            )
            raise

        logger.info(f"Channel {token} in organization {alert_receive_channel.organization.public_primary_key} is moved")
        raise OrganizationMovedException(alert_receive_channel.organization)
