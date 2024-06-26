from dataclasses import asdict

from rest_framework import serializers

from apps.base.messaging import get_messaging_backend_from_id
from apps.base.models import LiveSetting
from apps.phone_notifications.phone_provider import get_phone_provider
from apps.slack.models import SlackTeamIdentity
from apps.user_management.models import Organization
from common.api_helpers.mixins import EagerLoadingMixin


class FastSlackTeamIdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = SlackTeamIdentity
        fields = ["cached_name"]


class OrganizationSerializer(EagerLoadingMixin, serializers.ModelSerializer):
    pk = serializers.CharField(read_only=True, source="public_primary_key")
    slack_team_identity = FastSlackTeamIdentitySerializer(read_only=True)

    name = serializers.CharField(required=False, allow_null=True, allow_blank=True, source="org_title")
    slack_channel = serializers.SerializerMethodField()

    rbac_enabled = serializers.BooleanField(read_only=True, source="is_rbac_permissions_enabled")
    grafana_incident_enabled = serializers.BooleanField(read_only=True, source="is_grafana_incident_enabled")

    SELECT_RELATED = ["slack_team_identity"]

    class Meta:
        model = Organization
        fields = [
            "pk",
            "name",
            "stack_slug",
            "slack_team_identity",
            "slack_channel",
            "rbac_enabled",
            "grafana_incident_enabled",
        ]
        read_only_fields = [
            "stack_slug",
            "slack_team_identity",
            "rbac_enabled",
            "grafana_incident_enabled",
        ]

    def get_slack_channel(self, obj):
        from apps.slack.models import SlackChannel

        if obj.general_log_channel_id is None or obj.slack_team_identity is None:
            return None
        try:
            channel = obj.slack_team_identity.get_cached_channels().get(slack_id=obj.general_log_channel_id)
        except SlackChannel.DoesNotExist:
            return {"display_name": None, "slack_id": obj.general_log_channel_id, "id": None}

        return {
            "display_name": channel.name,
            "slack_id": channel.slack_id,
            "id": channel.public_primary_key,
        }


class CurrentOrganizationSerializer(OrganizationSerializer):
    env_status = serializers.SerializerMethodField()
    banner = serializers.SerializerMethodField()

    class Meta(OrganizationSerializer.Meta):
        fields = [
            *OrganizationSerializer.Meta.fields,
            "is_resolution_note_required",
            "env_status",
            "banner",
        ]
        read_only_fields = [
            *OrganizationSerializer.Meta.read_only_fields,
            "banner",
        ]

    def get_banner(self, obj):
        from apps.base.models import DynamicSetting

        banner = DynamicSetting.objects.get_or_create(
            name="banner",
            defaults={"json_value": {"title": None, "body": None}},
        )[0]
        return banner.json_value

    def get_env_status(self, obj):
        # deprecated in favour of ConfigAPIView.
        # All new env statuses should be added there
        LiveSetting.populate_settings_if_needed()

        telegram_configured = not LiveSetting.objects.filter(name__startswith="TELEGRAM", error__isnull=False).exists()
        phone_provider_config = get_phone_provider().flags
        return {
            "telegram_configured": telegram_configured,
            "phone_provider": asdict(phone_provider_config),
        }


class FastOrganizationSerializer(serializers.ModelSerializer):
    pk = serializers.CharField(read_only=True, source="public_primary_key")
    name = serializers.CharField(read_only=True, source="org_title")

    class Meta:
        model = Organization
        fields = ["pk", "name"]


class CurrentOrganizationConfigChecksSerializer(serializers.ModelSerializer):
    is_chatops_connected = serializers.SerializerMethodField()
    is_integration_chatops_connected = serializers.SerializerMethodField()
    mattermost = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "is_chatops_connected",
            "is_integration_chatops_connected",
            "mattermost",
        ]

    def get_mattermost(self, obj):
        env_status = not LiveSetting.objects.filter(name__startswith="MATTERMOST", error__isnull=False).exists()
        return {
            "env_status": env_status,
            "is_integrated": False,  # TODO: Add logic to verify if mattermost is integrated
        }

    def get_is_chatops_connected(self, obj):
        msteams_backend = get_messaging_backend_from_id("MSTEAMS")
        return bool(
            obj.slack_team_identity_id is not None  # slack is connected
            or obj.telegram_channel.exists()  # telegram is connected
            or (msteams_backend and msteams_backend.is_configured_for_organization(obj))  # msteams is connected
        )

    def get_is_integration_chatops_connected(self, obj):
        return (
            (
                obj.slack_team_identity_id is not None
                and obj.alert_receive_channels.filter(channel_filters__notify_in_slack=True).exists()
            )
            or obj.alert_receive_channels.filter(channel_filters__notify_in_telegram=True).exists()
            or obj.alert_receive_channels.filter(channel_filters__notification_backends__MSTEAMS__enabled=True).exists()
        )
