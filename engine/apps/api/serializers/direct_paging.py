import typing

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from apps.alerts.models import AlertGroup
from apps.user_management.models import Organization
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField
from common.api_helpers.utils import CurrentTeamDefault


class SerializerContext(typing.TypedDict):
    organization: Organization


class UserReferenceSerializer(serializers.Serializer):
    context: SerializerContext

    id = serializers.CharField()
    important = serializers.BooleanField()
    instance = serializers.HiddenField(default=None)  # set in UserReferenceSerializer.validate

    def validate(self, attrs):
        id = attrs["id"]
        organization = self.context["organization"]

        try:
            attrs["instance"] = organization.users.get(public_primary_key=id)
        except ObjectDoesNotExist:
            raise serializers.ValidationError(f"User {id} does not exist")

        return attrs


class BasePagingSerializer(serializers.Serializer):
    context: SerializerContext

    ALLOWS_GRAFANA_INCIDENT_ID = False

    users = UserReferenceSerializer(many=True, required=False, default=list)
    team = TeamPrimaryKeyRelatedField(allow_null=True, default=CurrentTeamDefault())
    important_team_escalation = serializers.BooleanField(required=False, default=False)

    alert_group_id = serializers.CharField(required=False, default=None)
    alert_group = serializers.HiddenField(default=None)  # set in DirectPagingSerializer.validate

    title = serializers.CharField(required=False, default=None)
    message = serializers.CharField(required=False, default=None, allow_null=True)
    source_url = serializers.URLField(required=False, default=None, allow_null=True)

    def validate(self, attrs):
        organization = self.context["organization"]
        alert_group_id = attrs["alert_group_id"]
        title = attrs["title"]
        message = attrs["message"]
        source_url = attrs["source_url"]
        grafana_incident_id = self.ALLOWS_GRAFANA_INCIDENT_ID and attrs.get("grafana_incident_id")

        if alert_group_id and (title or message or source_url or grafana_incident_id):
            raise serializers.ValidationError(
                f"alert_group_id and (title, message, source_url{', grafana_incident_id' if self.ALLOWS_GRAFANA_INCIDENT_ID else ''}) "
                "are mutually exclusive"
            )

        if attrs["users"] and attrs["team"]:
            raise serializers.ValidationError("users and team are mutually exclusive")

        if alert_group_id:
            try:
                attrs["alert_group"] = AlertGroup.objects.get(
                    public_primary_key=alert_group_id, channel__organization=organization
                )
            except ObjectDoesNotExist:
                raise serializers.ValidationError("Alert group {} does not exist".format(alert_group_id))

        return attrs


class DirectPagingSerializer(BasePagingSerializer):
    ALLOWS_GRAFANA_INCIDENT_ID = True

    grafana_incident_id = serializers.CharField(required=False, default=None, allow_null=True)
