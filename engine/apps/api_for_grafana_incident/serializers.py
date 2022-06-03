import logging

from rest_framework import serializers

from apps.alerts.models import AlertGroup
from common.api_helpers.mixins import EagerLoadingMixin

logger = logging.getLogger(__name__)


class AlertGroupSerializer(EagerLoadingMixin, serializers.ModelSerializer):

    id_oncall = serializers.CharField(read_only=True, source="public_primary_key")
    status = serializers.SerializerMethodField(source="get_status")
    link = serializers.CharField(read_only=True, source="web_link")

    def get_status(self, obj):
        return next(filter(lambda status: status[0] == obj.status, AlertGroup.STATUS_CHOICES))[1].lower()

    class Meta:
        model = AlertGroup
        fields = [
            "id_oncall",
            "link",
            "status",
        ]
