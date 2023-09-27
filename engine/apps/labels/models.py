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


LabelsData = typing.List[LabelData]


class LabelKeyData(typing.TypedDict):
    key: LabelParams
    values: typing.List[LabelParams]


def get_associating_label_model(model):
    class_name = model.__name__ + ASSOCIATED_MODEL_NAME
    label_model = apps.get_model(model._meta.app_label, class_name)
    return label_model


class LabelKeyCache(models.Model):
    id = models.CharField(primary_key=True, editable=False, max_length=36)
    repr = models.CharField(max_length=200)
    organization = models.ForeignKey("user_management.Organization", on_delete=models.CASCADE)
    last_synced = models.DateTimeField(auto_now=True)

    @property
    def is_outdated(self):
        return timezone.now() - self.last_synced > timezone.timedelta(minutes=5)


class LabelValueCache(models.Model):
    id = models.CharField(primary_key=True, editable=False, max_length=36)
    repr = models.CharField(max_length=200)
    key = models.ForeignKey("labels.LabelKeyCache", on_delete=models.CASCADE, related_name="values")
    last_synced = models.DateTimeField(auto_now=True)

    @property
    def is_outdated(self):
        return timezone.now() - self.last_synced > timezone.timedelta(minutes=5)


class AssociatedLabel(models.Model):
    key = models.ForeignKey(LabelKeyCache, on_delete=models.CASCADE)
    value = models.ForeignKey(LabelValueCache, on_delete=models.CASCADE)
    organization = models.ForeignKey("user_management.Organization", on_delete=models.CASCADE, related_name="labels")

    class Meta:
        abstract = True

    @staticmethod
    def associate(labels_data: LabelsData, instance: models.Model, organization: "Organization"):
        for label_data in labels_data:
            key_id = label_data["key"]["id"]
            key_repr = label_data["key"]["repr"]
            value_id = label_data["value"]["id"]
            value_repr = label_data["value"]["repr"]

            label_key, _ = LabelKeyCache.objects.update_or_create(
                id=key_id, organization=organization, defaults={"repr": key_repr}
            )
            label_value, _ = label_key.values.update_or_create(id=value_id, defaults={"repr": value_repr})
            label, _ = instance.labels.get_or_create(key=label_key, value=label_value, organization=organization)

    @staticmethod
    def update_association(labels_data: LabelsData, instance: models.Model, organization: "Organization"):
        # now = timezone.now()
        labels_keys = {label["key"]["id"]: label["key"]["repr"] for label in labels_data}
        labels_values = {label["value"]["id"]: label["value"]["repr"] for label in labels_data}

        associated_labels = instance.labels.all()

        # delete associations with labels that are not presented in labels_data
        associated_labels.exclude(key_id__in=labels_keys.keys(), value_id__in=labels_values.keys()).delete()

        labels_keys = []
        labels_values = []
        labels_associations = []

        for label_data in labels_data:
            key_id = label_data["key"]["id"]
            key_repr = label_data["key"]["repr"]
            value_id = label_data["value"]["id"]
            value_repr = label_data["value"]["repr"]

            label_key = LabelKeyCache(id=key_id, repr=key_repr, organization=organization)
            labels_keys.append(label_key)

            label_value = LabelValueCache(id=value_id, repr=value_repr, key_id=key_id)
            labels_values.append(label_value)
            associated_instance = {instance.labels.model.associated_instance_field: instance}
            labels_associations.append(
                instance.labels.model(
                    key_id=key_id, value_id=value_id, organization=organization, **associated_instance
                )
            )

        LabelKeyCache.objects.bulk_create(labels_keys, ignore_conflicts=True, batch_size=5000)
        LabelValueCache.objects.bulk_create(labels_values, ignore_conflicts=True, batch_size=5000)
        instance.labels.model.objects.bulk_create(labels_associations, ignore_conflicts=True, batch_size=5000)

    @staticmethod
    def remove(label_data, instance):
        # todo: if not associated?
        key_id = label_data["key"]["id"]
        value_id = label_data["value"]["id"]
        instance.labels.filter(key_id=key_id, value_id=value_id).delete()
        # todo: delete unused cache


class AlertReceiveChannelAssociatedLabel(AssociatedLabel):
    associated_instance_field = "alert_receive_channel"

    alert_receive_channel = models.ForeignKey(
        "alerts.AlertReceiveChannel", on_delete=models.CASCADE, related_name="labels"
    )

    class Meta:
        unique_together = ["key_id", "value_id", "alert_receive_channel_id"]
