from rest_framework import serializers

from apps.alerts.models import AlertGroup
from common.api_helpers.mixins import EagerLoadingMixin


class IncidentSerializer(EagerLoadingMixin, serializers.ModelSerializer):

    id = serializers.CharField(read_only=True, source="public_primary_key")
    integration_id = serializers.CharField(source="channel.public_primary_key")
    route_id = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(source="started_at")
    alerts_count = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()

    SELECT_RELATED = ["channel", "channel_filter"]
    PREFETCH_RELATED = ["alerts"]

    class Meta:
        model = AlertGroup
        fields = [
            "id",
            "integration_id",
            "route_id",
            "alerts_count",
            "state",
            "created_at",
            "resolved_at",
            "acknowledged_at",
            "title",
            "permalink",
        ]

    def get_alerts_count(self, obj):
        return len(obj.alerts.all())

    def get_title(self, obj):
        return obj.alerts.all()[0].title

    def get_state(self, obj):
        return obj.state

    def get_route_id(self, obj):
        if obj.channel_filter is not None:
            return obj.channel_filter.public_primary_key
        else:
            return None
