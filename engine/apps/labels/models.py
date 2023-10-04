import typing

from django.db import models
from django.utils import timezone

from apps.labels.tasks import update_labels_cache
from apps.labels.utils import LABEL_OUTDATED_TIMEOUT_MINUTES, LabelsData

if typing.TYPE_CHECKING:
    from apps.user_management.models import Organization


class LabelKeyCache(models.Model):
    id = models.CharField(primary_key=True, editable=False, max_length=36)
    repr = models.CharField(max_length=200)
    organization = models.ForeignKey("user_management.Organization", on_delete=models.CASCADE)
    last_synced = models.DateTimeField(auto_now=True)

    @property
    def is_outdated(self) -> bool:
        return timezone.now() - self.last_synced > timezone.timedelta(minutes=LABEL_OUTDATED_TIMEOUT_MINUTES)


class LabelValueCache(models.Model):
    id = models.CharField(primary_key=True, editable=False, max_length=36)
    repr = models.CharField(max_length=200)
    key = models.ForeignKey("labels.LabelKeyCache", on_delete=models.CASCADE, related_name="values")
    last_synced = models.DateTimeField(auto_now=True)

    @property
    def is_outdated(self) -> bool:
        return timezone.now() - self.last_synced > timezone.timedelta(minutes=LABEL_OUTDATED_TIMEOUT_MINUTES)


class AssociatedLabel(models.Model):
    key = models.ForeignKey(LabelKeyCache, on_delete=models.CASCADE)
    value = models.ForeignKey(LabelValueCache, on_delete=models.CASCADE)
    organization = models.ForeignKey("user_management.Organization", on_delete=models.CASCADE, related_name="labels")

    class Meta:
        abstract = True

    @staticmethod
    def update_association(labels_data: "LabelsData", instance: models.Model, organization: "Organization") -> None:
        labels_data_keys = {label["key"]["id"]: label["key"]["repr"] for label in labels_data}
        labels_data_values = {label["value"]["id"]: label["value"]["repr"] for label in labels_data}

        # delete associations with labels that are not presented in labels_data
        instance.labels.exclude(key_id__in=labels_data_keys.keys(), value_id__in=labels_data_values.keys()).delete()

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

        update_labels_cache.apply_async((labels_data,))


class AlertReceiveChannelAssociatedLabel(AssociatedLabel):
    associated_instance_field = "alert_receive_channel"

    alert_receive_channel = models.ForeignKey(
        "alerts.AlertReceiveChannel", on_delete=models.CASCADE, related_name="labels"
    )

    class Meta:
        unique_together = ["key_id", "value_id", "alert_receive_channel_id"]
