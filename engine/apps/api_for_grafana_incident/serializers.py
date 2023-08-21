import logging

from rest_framework import serializers

from apps.alerts.models import Alert, AlertGroup

logger = logging.getLogger(__name__)


class AlertSerializer(serializers.ModelSerializer):
    id_oncall = serializers.CharField(read_only=True, source="public_primary_key")
    payload = serializers.JSONField(read_only=True, source="raw_request_data")

    class Meta:
        model = Alert
        fields = [
            "id_oncall",
            "payload",
        ]


class AlertGroupSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    status = serializers.SerializerMethodField(source="get_status")
    link = serializers.CharField(read_only=True, source="web_link")
    title = serializers.CharField(read_only=True, source="long_verbose_name_without_formatting")
    alerts = AlertSerializer(many=True, read_only=True)

    def get_status(self, obj):
        return next(filter(lambda status: status[0] == obj.status, AlertGroup.STATUS_CHOICES))[1].lower()

    class Meta:
        model = AlertGroup
        fields = [
            "id",
            "link",
            "status",
            "alerts",
            "title",
        ]
