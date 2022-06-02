from django.db import models


class LockedAlert(models.Model):
    alert = models.OneToOneField("alerts.Alert", on_delete=models.CASCADE, related_name="migrator_lock")
