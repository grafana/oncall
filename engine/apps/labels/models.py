from django.apps import apps  # noqa: I251
from django.db import models
from django.utils import timezone

ASSOCIATED_MODEL_NAME = "AssociatedLabel"


def get_associating_label_model(model):
    class_name = model.__name__ + ASSOCIATED_MODEL_NAME
    label_model = apps.get_model(model._meta.app_label, class_name)
    return label_model


class LabelKeyCache(models.Model):
    key_id = models.CharField(primary_key=True, editable=False, max_length=30)
    key_repr = models.CharField(max_length=50)
    organization = models.ForeignKey("user_management.Organization", on_delete=models.CASCADE)
    last_synced = models.DateTimeField(auto_now=True)

    @property
    def is_outdated(self):
        return timezone.now() - self.last_synced > timezone.timedelta(minutes=5)


class LabelValueCache(models.Model):
    value_id = models.CharField(primary_key=True, editable=False, max_length=30)
    value_repr = models.CharField(max_length=50)
    key = models.ForeignKey("labels.LabelKeyCache", on_delete=models.CASCADE, related_name="values")
    last_synced = models.DateTimeField(auto_now=True)

    class Meta:
        pass

    @property
    def is_outdated(self):
        return timezone.now() - self.last_synced > timezone.timedelta(minutes=5)


class Label(models.Model):
    key = models.ForeignKey(LabelKeyCache, on_delete=models.CASCADE)
    value = models.ForeignKey(LabelValueCache, on_delete=models.CASCADE)
    organization = models.ForeignKey("user_management.Organization", on_delete=models.CASCADE, related_name="labels")

    class Meta:
        abstract = True

    @staticmethod
    def associate(key_id, value_id, instance, organization):
        # todo: if already associated
        label, _ = Label.objects.get_or_create(key_id=key_id, value_id=value_id, organization=organization)
        instance.labels.add(label)

    @staticmethod
    def remove(key_id, value_id, instance, organization):
        # todo: if not associated
        label = Label.objects.filter(key_id=key_id, value_id=value_id, organization=organization).first()
        if label:
            instance.labels.remove(label)


class AlertReceiveChannelAssociatedLabel(Label):
    alert_receive_channel = models.ForeignKey("alerts.AlertReceiveChannel", on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(fields=["key_id", "value_id", "alert_receive_channel_id"]),
        ]
