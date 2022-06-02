from rest_framework import serializers

from apps.alerts.models import Alert
from common.api_helpers.mixins import EagerLoadingMixin


class AlertSerializer(EagerLoadingMixin, serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    alert_group_id = serializers.CharField(read_only=True, source="group.public_primary_key")
    payload = serializers.JSONField(read_only=True, source="raw_request_data")

    SELECT_RELATED = ["group"]

    class Meta:
        model = Alert
        fields = [
            "id",
            "alert_group_id",
            "created_at",
            "payload",
        ]
