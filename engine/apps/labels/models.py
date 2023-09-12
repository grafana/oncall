from django.db import models


class Label(models.Model):
    key_id = models.CharField(max_length=20)
    value_id = models.CharField(max_length=20)
    organization = models.ForeignKey("user_management.Organization", on_delete=models.CASCADE, related_name="labels")

    class Meta:
        unique_together = ("key_id", "value_id", "organization")

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


class AlertReceiveChannelAssociatedLabel(models.Model):
    label = models.ForeignKey(Label, on_delete=models.CASCADE)
    alert_receive_channel = models.ForeignKey("alerts.AlertReceiveChannel", on_delete=models.CASCADE)
