from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from apps.alerts.models import AlertGroup
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField
from common.api_helpers.utils import CurrentTeamDefault


class UserReferenceSerializer(serializers.Serializer):
    id = serializers.CharField()
    important = serializers.BooleanField()
    instance = serializers.HiddenField(default=None)  # set in UserReferenceSerializer.validate

    def validate(self, attrs):
        organization = self.context["organization"]

        try:
            attrs["instance"] = organization.users.get(public_primary_key=attrs["id"])
        except ObjectDoesNotExist:
            raise serializers.ValidationError("User {} does not exist".format(attrs["id"]))

        return attrs


class ScheduleReferenceSerializer(serializers.Serializer):
    id = serializers.CharField()
    important = serializers.BooleanField()
    instance = serializers.HiddenField(default=None)  # set in ScheduleReferenceSerializer.validate

    def validate(self, attrs):
        organization = self.context["organization"]

        try:
            attrs["instance"] = organization.oncall_schedules.get(public_primary_key=attrs["id"])
        except ObjectDoesNotExist:
            raise serializers.ValidationError("Schedule {} does not exist".format(attrs["id"]))

        return attrs


class DirectPagingSerializer(serializers.Serializer):
    users = UserReferenceSerializer(many=True, required=False, default=list)
    schedules = ScheduleReferenceSerializer(many=True, required=False, default=list)

    escalation_chain_id = serializers.CharField(required=False, default=None)
    escalation_chain = serializers.HiddenField(default=None)  # set in DirectPagingSerializer.validate

    alert_group_id = serializers.CharField(required=False, default=None)
    alert_group = serializers.HiddenField(default=None)  # set in DirectPagingSerializer.validate

    title = serializers.CharField(required=False, default=None)
    message = serializers.CharField(required=False, default=None, allow_null=True)

    team = TeamPrimaryKeyRelatedField(allow_null=True, default=CurrentTeamDefault())

    def validate(self, attrs):
        organization = self.context["organization"]

        escalation_chain_id = attrs["escalation_chain_id"]

        alert_group_id = attrs["alert_group_id"]
        title = attrs["title"]
        message = attrs["message"]

        if alert_group_id and (title or message):
            raise serializers.ValidationError("alert_group_id and (title, message) are mutually exclusive")

        if alert_group_id and escalation_chain_id:
            raise serializers.ValidationError("escalation_chain_id is not supported for existing alert groups")

        if alert_group_id:
            try:
                attrs["alert_group"] = AlertGroup.objects.get(
                    public_primary_key=alert_group_id, channel__organization=organization
                )
            except ObjectDoesNotExist:
                raise serializers.ValidationError("Alert group {} does not exist".format(alert_group_id))

        if escalation_chain_id:
            try:
                attrs["escalation_chain"] = organization.escalation_chains.get(public_primary_key=escalation_chain_id)
            except ObjectDoesNotExist:
                raise serializers.ValidationError("Escalation chain {} does not exist".format(escalation_chain_id))

        return attrs
