import logging

from rest_framework import serializers

from apps.alerts.incident_appearance.renderers.web_renderer import AlertGroupWebRenderer
from apps.alerts.incident_appearance.renderers.classic_markdown_renderer import AlertGroupClassicMarkdownRenderer
from apps.alerts.models import AlertGroup
from common.api_helpers.mixins import EagerLoadingMixin

from .alert import AlertSerializer
from .alert_receive_channel import FastAlertReceiveChannelSerializer
from .user import FastUserSerializer

logger = logging.getLogger(__name__)


class ShortAlertGroupSerializer(serializers.ModelSerializer):
    pk = serializers.CharField(read_only=True, source="public_primary_key")
    alert_receive_channel = FastAlertReceiveChannelSerializer(source="channel")
    render_for_web = serializers.SerializerMethodField()

    class Meta:
        model = AlertGroup
        fields = ["pk", "render_for_web", "alert_receive_channel", "inside_organization_number"]

    def get_render_for_web(self, obj):
        return AlertGroupWebRenderer(obj).render()


class AlertGroupListSerializer(EagerLoadingMixin, serializers.ModelSerializer):
    pk = serializers.CharField(read_only=True, source="public_primary_key")
    alert_receive_channel = FastAlertReceiveChannelSerializer(source="channel")
    status = serializers.ReadOnlyField()
    resolved_by_user = FastUserSerializer(required=False)
    acknowledged_by_user = FastUserSerializer(required=False)
    silenced_by_user = FastUserSerializer(required=False)
    related_users = serializers.SerializerMethodField()
    dependent_alert_groups = ShortAlertGroupSerializer(many=True)
    root_alert_group = ShortAlertGroupSerializer()

    alerts_count = serializers.IntegerField(read_only=True)
    render_for_web = serializers.SerializerMethodField()
    render_for_classic_markdown = serializers.SerializerMethodField()

    PREFETCH_RELATED = [
        "dependent_alert_groups",
        "log_records__author",
    ]

    SELECT_RELATED = [
        "channel__organization",
        "root_alert_group",
        "resolved_by_user",
        "acknowledged_by_user",
        "silenced_by_user",
    ]

    class Meta:
        model = AlertGroup
        fields = [
            "pk",
            "alerts_count",
            "inside_organization_number",
            "verbose_name",
            "alert_receive_channel",
            "resolved",
            "resolved_by",
            "resolved_by_user",
            "resolved_at",
            "acknowledged_at",
            "acknowledged",
            "acknowledged_on_source",
            "acknowledged_at",
            "acknowledged_by_user",
            "silenced",
            "silenced_by_user",
            "silenced_at",
            "silenced_until",
            "started_at",
            "silenced_until",
            "related_users",
            "render_for_web",
            "render_for_classic_markdown",
            "dependent_alert_groups",
            "root_alert_group",
            "status",
        ]

    def get_render_for_web(self, obj):
        return AlertGroupWebRenderer(obj, obj.last_alert).render()

    def get_render_for_classic_markdown(self, obj):
        return AlertGroupClassicMarkdownRenderer(obj).render()

    def get_related_users(self, obj):
        users_ids = set()
        users = []

        # add resolved and acknowledged by_user explicitly because logs are already prefetched
        # when def acknowledge/resolve are called in view.
        if obj.resolved_by_user:
            users_ids.add(obj.resolved_by_user.public_primary_key)
            users.append(obj.resolved_by_user.short())

        if obj.acknowledged_by_user and obj.acknowledged_by_user.public_primary_key not in users_ids:
            users_ids.add(obj.acknowledged_by_user.public_primary_key)
            users.append(obj.acknowledged_by_user.short())

        if obj.silenced_by_user and obj.silenced_by_user.public_primary_key not in users_ids:
            users_ids.add(obj.silenced_by_user.public_primary_key)
            users.append(obj.silenced_by_user.short())

        for log_record in obj.log_records.all():
            if log_record.author is not None and log_record.author.public_primary_key not in users_ids:
                users.append(log_record.author.short())
                users_ids.add(log_record.author.public_primary_key)
        return users


class AlertGroupSerializer(AlertGroupListSerializer):
    alerts = serializers.SerializerMethodField("get_limited_alerts")
    last_alert_at = serializers.SerializerMethodField()

    class Meta(AlertGroupListSerializer.Meta):
        fields = AlertGroupListSerializer.Meta.fields + [
            "alerts",
            "render_after_resolve_report_json",
            "permalink",
            "last_alert_at",
        ]

    def get_render_for_web(self, obj):
        return AlertGroupWebRenderer(obj).render()

    def get_last_alert_at(self, obj):
        last_alert = obj.alerts.last()

        if not last_alert:
            return obj.started_at

        return last_alert.created_at

    def get_limited_alerts(self, obj):
        """
        Overriding default alerts because there are alert_groups with thousands of them.
        It's just too slow, we need to cut here.
        """
        alerts = obj.alerts.all()[:100]

        if len(alerts) > 90:
            for alert in alerts:
                alert.title = str(alert.title) + " Only last 100 alerts are shown. Use OnCall API to fetch all of them."

        return AlertSerializer(alerts, many=True).data
