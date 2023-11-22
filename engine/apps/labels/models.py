import typing

from django.db import models
from django.utils import timezone

from apps.labels.tasks import update_labels_cache
from apps.labels.utils import LABEL_OUTDATED_TIMEOUT_MINUTES, LabelsData

if typing.TYPE_CHECKING:
    from apps.user_management.models import Organization


class LabelKeyCache(models.Model):
    id = models.CharField(primary_key=True, editable=False, max_length=36)
    name = models.CharField(max_length=200)
    organization = models.ForeignKey("user_management.Organization", on_delete=models.CASCADE)
    last_synced = models.DateTimeField(auto_now=True)

    @property
    def is_outdated(self) -> bool:
        return timezone.now() - self.last_synced > timezone.timedelta(minutes=LABEL_OUTDATED_TIMEOUT_MINUTES)


class LabelValueCache(models.Model):
    id = models.CharField(primary_key=True, editable=False, max_length=36)
    name = models.CharField(max_length=200)
    key = models.ForeignKey("labels.LabelKeyCache", on_delete=models.CASCADE, related_name="values")
    last_synced = models.DateTimeField(auto_now=True)

    @property
    def is_outdated(self) -> bool:
        return timezone.now() - self.last_synced > timezone.timedelta(minutes=LABEL_OUTDATED_TIMEOUT_MINUTES)


class AssociatedLabel(models.Model):
    """
    Abstract model, is used to keep information about label association with other instances
    (integrations, schedules, etc.). To add ability to associate labels with a type of instances ,
    inhere this model and add a foreign key to the instance model.

    Attention: add `AssociatedLabel` to the end of the name of inheritor (example: AlertReceiveChannelAssociatedLabel)
    """

    key = models.ForeignKey(LabelKeyCache, on_delete=models.CASCADE)
    value = models.ForeignKey(LabelValueCache, on_delete=models.CASCADE)
    organization = models.ForeignKey("user_management.Organization", on_delete=models.CASCADE, related_name="labels")

    class Meta:
        abstract = True

    @staticmethod
    def update_association(labels_data: "LabelsData", instance: models.Model, organization: "Organization") -> None:
        """
        Update label associations for selected instance: delete associations with labels that are not in `labels_data`,
        create new associations and labels, if needed.
        Then call celery task to update cache for labels from `labels_data`

        instance: the model instance that the labels are associated with (e.g. AlertReceiveChannel instance)
        """
        labels_data_keys = {label["key"]["id"]: label["key"]["name"] for label in labels_data}
        labels_data_values = {label["value"]["id"]: label["value"]["name"] for label in labels_data}

        # delete associations with labels that are not presented in labels_data
        instance.labels.exclude(key_id__in=labels_data_keys.keys(), value_id__in=labels_data_values.keys()).delete()

        labels_keys = []
        labels_values = []
        labels_associations = []

        for label_data in labels_data:
            key_id = label_data["key"]["id"]
            key_name = label_data["key"]["name"]
            value_id = label_data["value"]["id"]
            value_name = label_data["value"]["name"]

            label_key = LabelKeyCache(id=key_id, name=key_name, organization=organization)
            labels_keys.append(label_key)

            label_value = LabelValueCache(id=value_id, name=value_name, key_id=key_id)
            labels_values.append(label_value)
            associated_instance = {instance.labels.field.name: instance}
            labels_associations.append(
                instance.labels.model(
                    key_id=key_id, value_id=value_id, organization=organization, **associated_instance
                )
            )

        # create labels cache and associations that don't exist
        LabelKeyCache.objects.bulk_create(labels_keys, ignore_conflicts=True, batch_size=5000)
        LabelValueCache.objects.bulk_create(labels_values, ignore_conflicts=True, batch_size=5000)
        instance.labels.model.objects.bulk_create(labels_associations, ignore_conflicts=True, batch_size=5000)

        update_labels_cache.apply_async((labels_data,))

    @staticmethod
    def get_associating_label_field_name() -> str:
        """Returns ForeignKey field name for the associated model"""
        raise NotImplementedError


class AlertReceiveChannelAssociatedLabel(AssociatedLabel):
    """Keeps information about label association with alert receive channel instances"""

    alert_receive_channel = models.ForeignKey(
        "alerts.AlertReceiveChannel", on_delete=models.CASCADE, related_name="labels"
    )

    # If inheritable is True, then the label will be passed down to alert groups
    inheritable = models.BooleanField(default=True, null=True)

    class Meta:
        unique_together = ["key_id", "value_id", "alert_receive_channel_id"]

    @staticmethod
    def get_associating_label_field_name() -> str:
        """Returns ForeignKey field name for the associated model"""
        return "alert_receive_channel"


class AlertGroupAssociatedLabel(models.Model):
    """
    A model for alert group labels (similar to AlertReceiveChannelAssociatedLabel for integrations).
    The key difference is that alert group labels do not use label IDs, but rather key and value names explicitly.
    This is done to make alert group labels "static" (so they don't change when the labels are updated in label repo).
    """

    alert_group = models.ForeignKey("alerts.AlertGroup", on_delete=models.CASCADE, related_name="labels")
    organization = models.ForeignKey(
        "user_management.Organization", on_delete=models.CASCADE, related_name="alert_group_labels"
    )

    key_name = models.CharField(max_length=200)
    value_name = models.CharField(max_length=200)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "key_name", "value_name", "alert_group"],
                name="unique_alert_group_label",
            )
        ]


class WebhookAssociatedLabel(AssociatedLabel):
    """Keeps information about label association with outgoing webhooks instances"""

    webhook = models.ForeignKey(
        "webhooks.Webhook",
        on_delete=models.CASCADE,
        related_name="labels",
    )
    organization = models.ForeignKey(
        "user_management.Organization", on_delete=models.CASCADE, related_name="webhook_labels"
    )

    class Meta:
        unique_together = ["key_id", "value_id", "webhook_id"]

    @staticmethod
    def get_associating_label_field_name() -> str:
        """Returns ForeignKey field name for the associated model"""
        return "webhook"
