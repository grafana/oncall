from rest_framework import serializers

from django.db.models import Prefetch
from apps.alerts.models import AlertGroup, Alert
from apps.api.serializers.alert_group import AlertGroupLabelSerializer
from apps.public_api.serializers.alerts import AlertSerializer
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField, UserIdField
from common.api_helpers.mixins import EagerLoadingMixin


class AlertGroupSerializer(EagerLoadingMixin, serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    integration_id = serializers.CharField(source="channel.public_primary_key")
    team_id = TeamPrimaryKeyRelatedField(source="channel.team", allow_null=True)
    route_id = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(source="started_at")
    alerts_count = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()
    acknowledged_by = UserIdField(read_only=True, source="acknowledged_by_user")
    resolved_by = UserIdField(read_only=True, source="resolved_by_user")
    labels = AlertGroupLabelSerializer(many=True, read_only=True)
    latest_alert = serializers.SerializerMethodField()

    SELECT_RELATED = ["channel", "channel_filter", "slack_message", "channel__organization", "channel__team"]
    PREFETCH_RELATED = ["labels"]
    PREFETCH_RELATED += [
        Prefetch(
            "alerts",
            queryset=Alert.objects.order_by("-created_at")[:1],
            to_attr="prefetched_last_alert",
        ),
    ]

    class Meta:
        model = AlertGroup
        fields = [
            "id",
            "integration_id",
            "team_id",
            "route_id",
            "alerts_count",
            "state",
            "created_at",
            "resolved_at",
            "resolved_by",
            "acknowledged_at",
            "acknowledged_by",
            "labels",
            "title",
            "permalinks",
            "silenced_at",
            "latest_alert",
        ]

    def get_title(self, obj):
        return obj.web_title_cache

    def get_alerts_count(self, obj):
        return obj.alerts.count()

    def get_state(self, obj):
        return obj.state

    def get_route_id(self, obj):
        if obj.channel_filter is not None:
            return obj.channel_filter.public_primary_key
        else:
            return None
        
    def get_latest_alert(self, obj):
        latest_alert = obj.prefetched_last_alert.order_by("-created_at").last()

        return AlertSerializer(latest_alert).data if latest_alert else None
