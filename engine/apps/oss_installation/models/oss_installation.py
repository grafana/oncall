import logging
import uuid

from django.db import models

logger = logging.getLogger(__name__)


class OssInstallation(models.Model):
    """
    OssInstallation is model to track installation of OSS OnCall version.
    """

    installation_id = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now=True)
    report_sent_at = models.DateTimeField(null=True, default=None)
