import typing

from django.apps import apps  # noqa: I251
from django.db import models
from django.utils import timezone

if typing.TYPE_CHECKING:
    from apps.user_management.models import Organization


ASSOCIATED_MODEL_NAME = "AssociatedLabel"


class LabelParams(typing.TypedDict):
    id: str
    repr: str


class LabelData(typing.TypedDict):
    key: LabelParams
    value: LabelParams


def get_associating_label_model(model):
    class_name = model.__name__ + ASSOCIATED_MODEL_NAME
    label_model = apps.get_model(model._meta.app_label, class_name)
    return label_model


class LabelKeyCache(models.Model):
    key_id = models.CharField(max_length=36)
    key_repr = models.CharField(max_length=200)
    organization = models.ForeignKey("user_management.Organization", on_delete=models.CASCADE)
    last_synced = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [
            "key_id",
            "organization_id",
        ]

    @property
    def is_outdated(self):
        return timezone.now() - self.last_synced > timezone.timedelta(minutes=5)


class LabelValueCache(models.Model):
    value_id = models.CharField(max_length=36)
    value_repr = models.CharField(max_length=200)
    key = models.ForeignKey("labels.LabelKeyCache", on_delete=models.CASCADE, related_name="values")
    last_synced = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [
            "value_id",
            "key_id",
        ]

    @property
    def is_outdated(self):
        return timezone.now() - self.last_synced > timezone.timedelta(minutes=5)


class Label(models.Model):
    key_cache = models.ForeignKey(LabelKeyCache, on_delete=models.CASCADE)
    value_cache = models.ForeignKey(LabelValueCache, on_delete=models.CASCADE)
    organization = models.ForeignKey("user_management.Organization", on_delete=models.CASCADE, related_name="labels")
    key_id = models.CharField(max_length=36)
    value_id = models.CharField(max_length=36)

    class Meta:
        abstract = True

    @staticmethod
    def associate(label_data: LabelData, instance: models.Model, organization: "Organization"):
        # todo: if already associated?
        key_id = label_data["key"]["id"]
        key_repr = label_data["key"]["repr"]
        value_id = label_data["value"]["id"]
        value_repr = label_data["value"]["repr"]

        label_key, _ = LabelKeyCache.objects.update_or_create(
            key_id=key_id, organization=organization, defaults={"key_repr": key_repr}
        )
        label_value, _ = label_key.values.update_or_create(value_id=value_id, defaults={"value_repr": value_repr})
        label, _ = instance.labels.get_or_create(
            key_cache=label_key,
            value_cache=label_value,
            key_id=key_id,
            value_id=value_id,
            organization=organization,
        )

    @staticmethod
    def remove(label_data, instance):
        # todo: if not associated?
        key_id = label_data["key"]["id"]
        value_id = label_data["value"]["id"]
        instance.labels.get(key_id=key_id, value_id=value_id).delete()
        # todo: delete unused cache


class AlertReceiveChannelAssociatedLabel(Label):
    alert_receive_channel = models.ForeignKey(
        "alerts.AlertReceiveChannel", on_delete=models.CASCADE, related_name="labels"
    )

    class Meta:
        unique_together = ["key_id", "value_id", "alert_receive_channel_id"]
