import uuid

from django.db import models


class OssInstallation(models.Model):
    installation_id = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now=True)
    report_sent_at = models.DateTimeField(null=True, default=None)
