import typing

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from apps.alerts.models import AlertGroup
from apps.user_management.models import Organization


class SerializerContext(typing.TypedDict):
    organization: Organization


class ReferenceSerializer(serializers.Serializer):
    context: SerializerContext

    id = serializers.CharField()
    important = serializers.BooleanField()
    instance = serializers.HiddenField(default=None)  # set in UserReferenceSerializer.validate

    def validate(self, attrs):
        id = attrs["id"]
        organization = self.context["organization"]

        try:
            related_manager = getattr(organization, self.ORGANIZATION_REFERENCE_ATTR)
            attrs["instance"] = related_manager.get(public_primary_key=id)
        except ObjectDoesNotExist:
            raise serializers.ValidationError(f"{self.OBJECT_NOUN} {id} does not exist")

        return attrs


class UserReferenceSerializer(ReferenceSerializer):
    OBJECT_NOUN = "User"
    ORGANIZATION_REFERENCE_ATTR = "users"


class TeamReferenceSerializer(ReferenceSerializer):
    OBJECT_NOUN = "Team"
    ORGANIZATION_REFERENCE_ATTR = "teams"


class DirectPagingSerializer(serializers.Serializer):
    context: SerializerContext

    users = UserReferenceSerializer(many=True, required=False, default=list)
    team = TeamReferenceSerializer(required=False)

    alert_group_id = serializers.CharField(required=False, default=None)
    alert_group = serializers.HiddenField(default=None)  # set in DirectPagingSerializer.validate

    message = serializers.CharField(required=False, default=None, allow_null=True)

    def validate(self, attrs):
        # TODO: validate that either users or team is set (a minimum of one must be set)

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
