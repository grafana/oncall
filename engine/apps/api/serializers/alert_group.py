import logging
from datetime import datetime

import humanize
from rest_framework import serializers

from apps.alerts.incident_appearance.renderers.web_renderer import AlertGroupWebRenderer
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


class AlertGroupSerializer(EagerLoadingMixin, serializers.ModelSerializer):
    """
    Attention: It's heavily cached. Make sure to invalidate alertgroup's web cache if you update the format!
    """

    pk = serializers.CharField(read_only=True, source="public_primary_key")
    alert_receive_channel = FastAlertReceiveChannelSerializer(source="channel")
    alerts = serializers.SerializerMethodField("get_limited_alerts")
    resolved_by_verbose = serializers.CharField(source="get_resolved_by_display")
    resolved_by_user = FastUserSerializer(required=False)
    acknowledged_by_user = FastUserSerializer(required=False)
    silenced_by_user = FastUserSerializer(required=False)
    related_users = serializers.SerializerMethodField()

    last_alert_at = serializers.SerializerMethodField()

    started_at_verbose = serializers.SerializerMethodField()
    acknowledged_at_verbose = serializers.SerializerMethodField()
    resolved_at_verbose = serializers.SerializerMethodField()
    silenced_at_verbose = serializers.SerializerMethodField()

    dependent_alert_groups = ShortAlertGroupSerializer(many=True)
    root_alert_group = ShortAlertGroupSerializer()

    alerts_count = serializers.ReadOnlyField()

    status = serializers.ReadOnlyField()

    PREFETCH_RELATED = [
        "alerts",
        "dependent_alert_groups",
        "log_records",
        "log_records__author",
        "log_records__escalation_policy",
        "log_records__invitation__invitee",
    ]

    SELECT_RELATED = [
        "slack_message",
        "channel__organization",
        "slack_message___slack_team_identity",
        "acknowledged_by_user",
        "resolved_by_user",
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
            "resolved_by_verbose",
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
            "silenced_at_verbose",
            "silenced_until",
            "started_at",
            "last_alert_at",
            "silenced_until",
            "permalink",
            "alerts",
            "related_users",
            "started_at_verbose",
            "acknowledged_at_verbose",
            "resolved_at_verbose",
            "render_for_web",
            "render_after_resolve_report_json",
            "dependent_alert_groups",
            "root_alert_group",
            "status",
        ]

    def get_last_alert_at(self, obj):
        last_alert = obj.alerts.last()
        # TODO: This is a Hotfix for 0.0.27
        if last_alert is None:
            logger.warning(f"obj {obj} doesn't have last_alert!")
            return ""
        return str(last_alert.created_at)

    def get_limited_alerts(self, obj):
        """
        Overriding default alerts because there are alert_groups with thousands of them.
        It's just too slow, we need to cut here.
        """
        alerts = obj.alerts.all()[:100]

        if len(alerts) > 90:
            for alert in alerts:
                alert.title = str(alert.title) + " Only last 100 alerts are shown. Use Amixr API to fetch all of them."

        return AlertSerializer(alerts, many=True).data

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

    def get_started_at_verbose(self, obj):
        started_at_verbose = None
        if obj.started_at is not None:
            started_at_verbose = humanize.naturaltime(
                datetime.now().replace(tzinfo=None) - obj.started_at.replace(tzinfo=None)
            )
        return started_at_verbose

    def get_acknowledged_at_verbose(self, obj):
        acknowledged_at_verbose = None
        if obj.acknowledged_at is not None:
            acknowledged_at_verbose = humanize.naturaltime(
                datetime.now().replace(tzinfo=None) - obj.acknowledged_at.replace(tzinfo=None)
            )  # TODO: Deal with timezones
        return acknowledged_at_verbose

    def get_resolved_at_verbose(self, obj):
        resolved_at_verbose = None
        if obj.resolved_at is not None:
            resolved_at_verbose = humanize.naturaltime(
                datetime.now().replace(tzinfo=None) - obj.resolved_at.replace(tzinfo=None)
            )  # TODO: Deal with timezones
        return resolved_at_verbose

    def get_silenced_at_verbose(self, obj):
        silenced_at_verbose = None
        if obj.silenced_at is not None:
            silenced_at_verbose = humanize.naturaltime(
                datetime.now().replace(tzinfo=None) - obj.silenced_at.replace(tzinfo=None)
            )  # TODO: Deal with timezones
        return silenced_at_verbose
