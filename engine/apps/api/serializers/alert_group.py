import logging

from django.core.cache import cache
from django.utils import timezone
from rest_framework import serializers

from apps.alerts.incident_appearance.renderers.classic_markdown_renderer import AlertGroupClassicMarkdownRenderer
from apps.alerts.incident_appearance.renderers.web_renderer import AlertGroupWebRenderer
from apps.alerts.models import AlertGroup, AlertGroupLogRecord
from apps.user_management.models import User
from common.api_helpers.mixins import EagerLoadingMixin

from .alert import AlertSerializer
from .alert_receive_channel import FastAlertReceiveChannelSerializer
from .user import FastUserSerializer

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class AlertGroupFieldsCacheSerializerMixin:
    @classmethod
    def get_or_set_web_template_field(
        cls,
        obj,
        last_alert,
        field_name,
        renderer_class,
        cache_lifetime=60 * 60 * 24,
    ):
        CACHE_KEY = f"{field_name}_alert_group_{obj.id}"
        cached_field = cache.get(CACHE_KEY, None)

        web_templates_modified_at = obj.channel.web_templates_modified_at
        last_alert_created_at = last_alert.created_at

        # use cache only if cache exists
        # and cache was created after the last alert created
        # and either web templates never modified
        # or cache was created after templates were modified
        if (
            cached_field is not None
            and cached_field.get("cache_created_at") > last_alert_created_at
            and (web_templates_modified_at is None or cached_field.get("cache_created_at") > web_templates_modified_at)
        ):
            field = cached_field.get(field_name)
        else:
            field = renderer_class(obj, last_alert).render()
            cache.set(CACHE_KEY, {"cache_created_at": timezone.now(), field_name: field}, cache_lifetime)

        return field


class ShortAlertGroupSerializer(AlertGroupFieldsCacheSerializerMixin, serializers.ModelSerializer):
    pk = serializers.CharField(read_only=True, source="public_primary_key")
    alert_receive_channel = FastAlertReceiveChannelSerializer(source="channel")
    render_for_web = serializers.SerializerMethodField()

    class Meta:
        model = AlertGroup
        fields = ["pk", "render_for_web", "alert_receive_channel", "inside_organization_number"]

    def get_render_for_web(self, obj):
        last_alert = obj.alerts.last()
        if last_alert is None:
            return {}
        return AlertGroupFieldsCacheSerializerMixin.get_or_set_web_template_field(
            obj,
            last_alert,
            "render_for_web",
            AlertGroupWebRenderer,
        )


class AlertGroupListSerializer(EagerLoadingMixin, AlertGroupFieldsCacheSerializerMixin, serializers.ModelSerializer):
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
            "declare_incident_link",
        ]

    def get_render_for_web(self, obj):
        if not obj.last_alert:
            return {}
        return AlertGroupFieldsCacheSerializerMixin.get_or_set_web_template_field(
            obj,
            obj.last_alert,
            "render_for_web",
            AlertGroupWebRenderer,
        )

    def get_render_for_classic_markdown(self, obj):
        if not obj.last_alert:
            return {}
        return AlertGroupFieldsCacheSerializerMixin.get_or_set_web_template_field(
            obj,
            obj.last_alert,
            "render_for_classic_markdown",
            AlertGroupClassicMarkdownRenderer,
        )

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
    paged_users = serializers.SerializerMethodField()

    class Meta(AlertGroupListSerializer.Meta):
        fields = AlertGroupListSerializer.Meta.fields + [
            "alerts",
            "render_after_resolve_report_json",
            "slack_permalink",  # TODO: make plugin frontend use "permalinks" field to get Slack link
            "permalinks",
            "last_alert_at",
            "paged_users",
        ]

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

    def get_paged_users(self, obj):
        users_ids = set()
        for log_record in obj.log_records.filter(
            type__in=(AlertGroupLogRecord.TYPE_DIRECT_PAGING, AlertGroupLogRecord.TYPE_UNPAGE_USER)
        ):
            # filter paging events, track still active escalations
            info = log_record.get_step_specific_info()
            user_id = info.get("user") if info else None
            if user_id is not None:
                users_ids.add(
                    user_id
                ) if log_record.type == AlertGroupLogRecord.TYPE_DIRECT_PAGING else users_ids.discard(user_id)

        users = [u.short() for u in User.objects.filter(public_primary_key__in=users_ids)]
        return users
