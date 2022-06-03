from django.db import IntegrityError, models
from django.db.models import JSONField


class DynamicSettingsManager(models.Manager):
    def get_or_create(self, defaults=None, **kwargs):
        """
        Using get_or_create inside celery task sometimes triggers making two identical DynamicSettings.
        E.g. https://gitlab.amixr.io/amixr/amixr/issues/843
        More info: https://stackoverflow.com/questions/17960593/multipleobjectsreturned-with-get-or-create
        Solution is to create UniqueConstraint on DynamicSetting.Name and catch IntegrityError.
        Django 3 has built-in check https://github.com/django/django/blob/master/django/db/models/query.py#L571
        As for now we are using Django 2.2 which has not.
        # TODO: remove this method when we will move to Django 3
        So it is overridden get_or_create to catch IntegrityError and just return object in this case.
        """
        try:
            return super(DynamicSettingsManager, self).get_or_create(defaults=defaults, **kwargs)
        except IntegrityError:
            try:
                return self.get(**kwargs), False
            except self.model.DoesNotExist:
                pass
            raise


class DynamicSetting(models.Model):
    objects = DynamicSettingsManager()

    name = models.CharField(max_length=100)
    boolean_value = models.BooleanField(null=True, default=None)
    numeric_value = models.IntegerField(null=True, default=None)
    json_value = JSONField(default=None, null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["name"], name="unique_dynamic_setting_name")]

    def __str__(self):
        return self.name
