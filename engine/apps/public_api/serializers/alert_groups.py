from django.db.models import Prefetch
from rest_framework import serializers

from apps.alerts.models import AlertGroup
from apps.api.serializers.alert_group import AlertGroupLabelSerializer
from apps.public_api.serializers.alerts import AlertSerializer
from apps.slack.models import SlackMessage
from apps.telegram.models import TelegramMessage
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
    last_alert = serializers.SerializerMethodField()

    SELECT_RELATED = [
        "channel",
        "channel_filter",
        "channel__organization",
        "channel__team",
        "acknowledged_by_user",
        "resolved_by_user",
    ]
    PREFETCH_RELATED = [
        "labels",
        Prefetch(
            "slack_messages",
            queryset=SlackMessage.objects.select_related("_slack_team_identity").order_by("created_at")[:1],
            to_attr="prefetched_slack_messages",
        ),
        Prefetch(
            "telegram_messages",
            queryset=TelegramMessage.objects.filter(
                chat_id__startswith="-", message_type=TelegramMessage.ALERT_GROUP_MESSAGE
            ).order_by("id")[:1],
            to_attr="prefetched_telegram_messages",
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
            "last_alert",
        ]

    def get_title(self, obj):
        return obj.web_title_cache

    def get_state(self, obj):
        return obj.state

    def get_route_id(self, obj):
        if obj.channel_filter is not None:
            return obj.channel_filter.public_primary_key
        else:
            return None

    def get_last_alert(self, obj):
        if hasattr(obj, "last_alert"):  # could be set by AlertGroupEnrichingMixin.enrich
            last_alert = obj.last_alert
        else:
            last_alert = obj.alerts.order_by("-created_at").first()

        if last_alert is None:
            return None

        return AlertSerializer(last_alert).data

    def get_alerts_count(self, obj):
        if hasattr(obj, "alerts_count"):  # could be set by AlertGroupEnrichingMixin.enrich
            return obj.alerts_count

        return obj.alerts.count()
