from rest_framework import serializers

from apps.alerts.models import Alert
from common.api_helpers.mixins import EagerLoadingMixin


class AlertSerializer(EagerLoadingMixin, serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    alert_group_id = serializers.CharField(read_only=True, source="group.public_primary_key")
    payload = serializers.SerializerMethodField(read_only=True)

    SELECT_RELATED = ["group"]

    class Meta:
        model = Alert
        fields = [
            "id",
            "alert_group_id",
            "created_at",
            "payload",
        ]

    def get_payload(self, obj):
        return {} if obj.group.is_restricted else obj.raw_request_data
