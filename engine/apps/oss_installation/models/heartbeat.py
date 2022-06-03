import logging

from django.db import models

from apps.base.utils import live_settings

logger = logging.getLogger(__name__)


class CloudHeartbeat(models.Model):
    integration_id = models.CharField(max_length=50)
    integration_url = models.URLField()
    success = models.BooleanField(default=False)

    @classmethod
    def status(cls):
        """
        status returns status of cloud heartbeat:
        True if it was successfully.
        False if it wasn't.
        None if it is disabled.
        """
        if live_settings.GRAFANA_CLOUD_ONCALL_HEARTBEAT_ENABLED:
            cloud_heartbeat = cls.objects.first()
            if cloud_heartbeat is None:
                return None
            return cloud_heartbeat.success
        else:
            return None
