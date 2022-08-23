from datetime import timedelta

import humanize
import pytz
from django.apps import apps
from django.conf import settings
from django.utils import timezone
from rest_framework import fields, serializers

from apps.base.models import LiveSetting
from apps.slack.models import SlackTeamIdentity
from apps.slack.tasks import resolve_archived_incidents_for_organization, unarchive_incidents_for_organization
from apps.user_management.models import Organization
from common.api_helpers.mixins import EagerLoadingMixin


class CustomDateField(fields.TimeField):
    def to_internal_value(self, data):
        try:
            archive_datetime = timezone.datetime.fromisoformat(data).astimezone(pytz.UTC)
        except (TypeError, ValueError):
            raise serializers.ValidationError({"archive_alerts_from": ["Invalid date format"]})
        if archive_datetime.date() >= timezone.now().date():
            raise serializers.ValidationError({"archive_alerts_from": ["Invalid date. Date must be less than today."]})
        return archive_datetime


class FastSlackTeamIdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = SlackTeamIdentity
        fields = ["cached_name"]


class OrganizationSerializer(EagerLoadingMixin, serializers.ModelSerializer):
    pk = serializers.CharField(read_only=True, source="public_primary_key")
    slack_team_identity = FastSlackTeamIdentitySerializer(read_only=True)

    name = serializers.CharField(required=False, allow_null=True, allow_blank=True, source="org_title")
    # name_slug = serializers.CharField(required=False, allow_null=True, allow_blank=False)
    maintenance_till = serializers.ReadOnlyField(source="till_maintenance_timestamp")
    slack_channel = serializers.SerializerMethodField()

    SELECT_RELATED = ["slack_team_identity"]

    class Meta:
        model = Organization
        fields = [
            "pk",
            "name",
            # "name_slug",
            # "is_new_version",
            "slack_team_identity",
            "maintenance_mode",
            "maintenance_till",
            # "incident_retention_web_report",
            # "number_of_employees",
            "slack_channel",
        ]
        read_only_fields = [
            "is_new_version",
            "slack_team_identity",
            "maintenance_mode",
            "maintenance_till",
            # "incident_retention_web_report",
        ]

    def get_slack_channel(self, obj):
        SlackChannel = apps.get_model("slack", "SlackChannel")
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
    limits = serializers.SerializerMethodField()
    env_status = serializers.SerializerMethodField()
    banner = serializers.SerializerMethodField()

    class Meta(OrganizationSerializer.Meta):
        fields = [
            *OrganizationSerializer.Meta.fields,
            "limits",
            "archive_alerts_from",
            "is_resolution_note_required",
            "env_status",
            "banner",
        ]
        read_only_fields = [
            *OrganizationSerializer.Meta.read_only_fields,
            "limits",
            "banner",
        ]

    def get_banner(self, obj):
        DynamicSetting = apps.get_model("base", "DynamicSetting")
        banner = DynamicSetting.objects.get_or_create(
            name="banner",
            defaults={"json_value": {"title": None, "body": None}},
        )[0]
        return banner.json_value

    def get_limits(self, obj):
        user = self.context["request"].user
        if not settings.OSS_INSTALLATION:
            return obj.notifications_limit_web_report(user)

        # show a version warning on OSS installations in case backend and frontend are different versions
        frontend_version = self.context["request"].headers.get("X-OnCall-Plugin-Version")
        backend_version = settings.VERSION
        version_warning = {}
        if backend_version and frontend_version and backend_version != frontend_version:
            text = (
                "Version mismatch! Please make sure you have the same versions of the Grafana OnCall plugin "
                "and Grafana OnCall engine, "
                "otherwise there could be issues with your Grafana OnCall installation! "
                f"Current plugin version: {frontend_version}, current engine version: {backend_version}. "
                "Please see the update instructions: "
                "https://grafana.com/docs/oncall/latest/open-source/#update-grafana-oncall-oss"
            )
            version_warning = {"period_title": "Version mismatch", "show_limits_warning": True, "warning_text": text}

        return version_warning or obj.notifications_limit_web_report(user)

    def get_env_status(self, obj):
        LiveSetting.populate_settings_if_needed()

        telegram_configured = not LiveSetting.objects.filter(name__startswith="TELEGRAM", error__isnull=False).exists()
        twilio_configured = not LiveSetting.objects.filter(name__startswith="TWILIO", error__isnull=False).exists()

        return {
            "telegram_configured": telegram_configured,
            "twilio_configured": twilio_configured,
        }

    def get_stats(self, obj):
        if isinstance(obj.cached_seconds_saved_by_amixr, int):
            verbal_time_saved_by_amixr = humanize.naturaldelta(timedelta(seconds=obj.cached_seconds_saved_by_amixr))
        else:
            verbal_time_saved_by_amixr = None

        result = {
            "grouped_percent": obj.cached_grouped_percent,
            "alerts_count": obj.cached_alerts_count,
            "noise_reduction": obj.cached_noise_reduction,
            "average_response_time": humanize.naturaldelta(obj.cached_average_response_time),
            "verbal_time_saved_by_amixr": verbal_time_saved_by_amixr,
        }

        return result

    def update(self, instance, validated_data):
        current_archive_date = instance.archive_alerts_from
        archive_alerts_from = validated_data.get("archive_alerts_from")

        result = super().update(instance, validated_data)
        if archive_alerts_from is not None and current_archive_date != archive_alerts_from:
            if current_archive_date > archive_alerts_from:
                unarchive_incidents_for_organization.apply_async(
                    (instance.pk,),
                )
            resolve_archived_incidents_for_organization.apply_async(
                (instance.pk,),
            )

        return result


class FastOrganizationSerializer(serializers.ModelSerializer):
    pk = serializers.CharField(read_only=True, source="public_primary_key")
    name = serializers.CharField(read_only=True, source="org_title")

    class Meta:
        model = Organization
        fields = ["pk", "name"]


class PluginOrganizationSerializer(serializers.ModelSerializer):
    pk = serializers.CharField(read_only=True, source="public_primary_key")
    grafana_token = serializers.CharField(write_only=True, source="api_token")

    class Meta:
        model = Organization
        fields = ["pk", "stack_id", "stack_slug", "grafana_url", "org_id", "org_slug", "org_title", "grafana_token"]
