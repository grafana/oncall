from django.db import models
from django.db.models import JSONField


class DynamicSetting(models.Model):
    name = models.CharField(max_length=100)
    boolean_value = models.BooleanField(null=True, default=None)
    numeric_value = models.IntegerField(null=True, default=None)
    json_value = JSONField(default=None, null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["name"], name="unique_dynamic_setting_name")]

    def __str__(self):
        return self.name
