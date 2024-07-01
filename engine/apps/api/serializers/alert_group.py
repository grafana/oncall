import datetime
import logging
import typing

from django.core.cache import cache
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.alerts.incident_appearance.renderers.web_renderer import AlertGroupWebRenderer
from apps.alerts.models import AlertGroup
from apps.alerts.models.alert_group import PagedUser
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField
from common.api_helpers.mixins import EagerLoadingMixin

from .alert import AlertSerializer
from .alert_receive_channel import FastAlertReceiveChannelSerializer
from .alerts_field_cache_buster_mixin import AlertsFieldCacheBusterMixin
from .user import FastUserSerializer, UserShortSerializer

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ExternalURL(typing.TypedDict):
    integration: str
    integration_type: str
    external_id: str
    url: str


class RenderForWeb(typing.TypedDict):
    title: str
    message: str
    image_url: str | None
    source_link: str | None


class EmptyRenderForWeb(typing.TypedDict):
    pass


class AlertGroupFieldsCacheSerializerMixin(AlertsFieldCacheBusterMixin):
    CACHE_KEY_FORMAT_TEMPLATE = "{field_name}_alert_group_{object_id}"

    @classmethod
    def get_or_set_web_template_field(
        cls,
        obj,
        last_alert,
        field_name,
        renderer_class,
        cache_lifetime=60 * 60 * 24,
    ):
        CACHE_KEY = cls.calculate_cache_key(field_name, obj)
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


class AlertGroupLabelSerializer(serializers.Serializer):
    class KeySerializer(serializers.Serializer):
        id = serializers.CharField(source="key_name")
        name = serializers.CharField(source="key_name")

    class ValueSerializer(serializers.Serializer):
        id = serializers.CharField(source="value_name")
        name = serializers.CharField(source="value_name")

    key = KeySerializer(source="*")
    value = ValueSerializer(source="*")


class ShortAlertGroupSerializer(AlertGroupFieldsCacheSerializerMixin, serializers.ModelSerializer):
    pk = serializers.CharField(read_only=True, source="public_primary_key")
    alert_receive_channel = FastAlertReceiveChannelSerializer(source="channel")
    render_for_web = serializers.SerializerMethodField()

    class Meta:
        model = AlertGroup
        fields = ["pk", "render_for_web", "alert_receive_channel", "inside_organization_number"]
        read_only_fields = ["pk", "render_for_web", "alert_receive_channel", "inside_organization_number"]

    def get_render_for_web(self, obj: "AlertGroup") -> RenderForWeb | EmptyRenderForWeb:
        last_alert = obj.alerts.last()
        if last_alert is None:
            return {}
        return AlertGroupFieldsCacheSerializerMixin.get_or_set_web_template_field(
            obj,
            last_alert,
            AlertGroupFieldsCacheSerializerMixin.RENDER_FOR_WEB_FIELD_NAME,
            AlertGroupWebRenderer,
        )


class AlertGroupListSerializer(
    EagerLoadingMixin, AlertGroupFieldsCacheSerializerMixin, serializers.ModelSerializer[AlertGroup]
):
    pk = serializers.CharField(read_only=True, source="public_primary_key")
    alert_receive_channel = FastAlertReceiveChannelSerializer(source="channel")
    status = serializers.ReadOnlyField()
    resolved_by_user = FastUserSerializer(required=False)
    acknowledged_by_user = FastUserSerializer(required=False)
    silenced_by_user = FastUserSerializer(required=False)
    related_users = serializers.SerializerMethodField()
    dependent_alert_groups = ShortAlertGroupSerializer(many=True)
    root_alert_group = ShortAlertGroupSerializer()
    team = TeamPrimaryKeyRelatedField(source="channel.team", allow_null=True)

    alerts_count = serializers.IntegerField(read_only=True)
    render_for_web = serializers.SerializerMethodField()

    labels = AlertGroupLabelSerializer(many=True, read_only=True)

    PREFETCH_RELATED = [
        "dependent_alert_groups",
        "log_records__author",
        "labels",
    ]

    SELECT_RELATED = [
        "channel__organization",
        "channel__team",
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
            "dependent_alert_groups",
            "root_alert_group",
            "status",
            "declare_incident_link",
            "team",
            "grafana_incident_id",
            "labels",
            "permalinks",
        ]

    def get_render_for_web(self, obj: "AlertGroup") -> RenderForWeb | EmptyRenderForWeb:
        if not obj.last_alert:
            return {}
        return AlertGroupFieldsCacheSerializerMixin.get_or_set_web_template_field(
            obj,
            obj.last_alert,
            AlertGroupFieldsCacheSerializerMixin.RENDER_FOR_WEB_FIELD_NAME,
            AlertGroupWebRenderer,
        )

    @extend_schema_field(UserShortSerializer(many=True))
    def get_related_users(self, obj: "AlertGroup"):
        from apps.user_management.models import User

        users_ids: typing.Set[str] = set()
        users: typing.List[User] = []

        # add resolved and acknowledged by_user explicitly because logs are already prefetched
        # when def acknowledge/resolve are called in view.
        if obj.resolved_by_user:
            users_ids.add(obj.resolved_by_user.public_primary_key)
            users.append(obj.resolved_by_user)

        if obj.acknowledged_by_user and obj.acknowledged_by_user.public_primary_key not in users_ids:
            users_ids.add(obj.acknowledged_by_user.public_primary_key)
            users.append(obj.acknowledged_by_user)

        if obj.silenced_by_user and obj.silenced_by_user.public_primary_key not in users_ids:
            users_ids.add(obj.silenced_by_user.public_primary_key)
            users.append(obj.silenced_by_user)

        for log_record in obj.log_records.all():
            if log_record.author is not None and log_record.author.public_primary_key not in users_ids:
                users.append(log_record.author)
                users_ids.add(log_record.author.public_primary_key)
        return UserShortSerializer(users, many=True).data


class AlertGroupSerializer(AlertGroupListSerializer):
    alerts = serializers.SerializerMethodField("get_limited_alerts")
    last_alert_at = serializers.SerializerMethodField()
    paged_users = serializers.SerializerMethodField()
    external_urls = serializers.SerializerMethodField()

    class Meta(AlertGroupListSerializer.Meta):
        fields = AlertGroupListSerializer.Meta.fields + [
            "alerts",
            "render_after_resolve_report_json",
            "slack_permalink",  # TODO: make plugin frontend use "permalinks" field to get Slack link
            "last_alert_at",
            "paged_users",
            "external_urls",
        ]

    def get_last_alert_at(self, obj: "AlertGroup") -> datetime.datetime:
        last_alert = obj.alerts.last()

        if not last_alert:
            return obj.started_at

        return last_alert.created_at

    @extend_schema_field(AlertSerializer(many=True))
    def get_limited_alerts(self, obj: "AlertGroup"):
        """
        Overriding default alerts because there are alert_groups with thousands of them.
        It's just too slow, we need to cut here.
        """
        alerts = obj.alerts.order_by("-pk")[:100]
        return AlertSerializer(alerts, many=True).data

    def get_paged_users(self, obj: "AlertGroup") -> typing.List[PagedUser]:
        return obj.get_paged_users()

    def get_external_urls(self, obj: "AlertGroup") -> typing.List[ExternalURL]:
        external_urls = []
        external_ids = obj.external_ids.all()
        for external_id in external_ids:
            source_integration = external_id.source_alert_receive_channel
            get_url = getattr(source_integration.config, "get_url", None)
            if get_url:
                url = source_integration.config.get_url(source_integration, external_id.value)
                external_urls.append(
                    {
                        "integration": source_integration.public_primary_key,
                        "integration_type": source_integration.integration,
                        "external_id": external_id.value,
                        "url": url,
                    }
                )
        return external_urls
