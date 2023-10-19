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


class DirectPagingSerializer(serializers.Serializer):
    context: SerializerContext

    users = UserReferenceSerializer(many=True, required=False, default=list)
    team = TeamPrimaryKeyRelatedField(allow_null=True, default=CurrentTeamDefault())

    alert_group_id = serializers.CharField(required=False, default=None)
    alert_group = serializers.HiddenField(default=None)  # set in DirectPagingSerializer.validate

    message = serializers.CharField(required=False, default=None, allow_null=True)

    def validate(self, attrs):
        organization = self.context["organization"]
        alert_group_id = attrs["alert_group_id"]
        message = attrs["message"]

        if alert_group_id and message:
            raise serializers.ValidationError("alert_group_id and message are mutually exclusive")

        if alert_group_id:
            try:
                attrs["alert_group"] = AlertGroup.objects.get(
                    public_primary_key=alert_group_id, channel__organization=organization
                )
            except ObjectDoesNotExist:
                raise serializers.ValidationError("Alert group {} does not exist".format(alert_group_id))

        return attrs
