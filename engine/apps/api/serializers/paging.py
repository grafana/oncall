from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from apps.alerts.models import AlertGroup


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

    alert_group_id = serializers.CharField(required=False, default=None)
    alert_group = serializers.HiddenField(default=None)  # set in DirectPagingSerializer.validate

    title = serializers.CharField(required=False, default=None)
    message = serializers.CharField(required=False, default=None)

    def validate(self, attrs):
        if len(attrs["users"]) == 0 and len(attrs["schedules"]) == 0:
            raise serializers.ValidationError("Provide at least one user or schedule")

        if attrs["alert_group_id"] and (attrs["title"] or attrs["message"]):
            raise serializers.ValidationError("alert_group_id and (title, message) are mutually exclusive")

        if attrs["alert_group_id"]:
            organization = self.context["organization"]
            try:
                attrs["alert_group"] = AlertGroup.unarchived_objects.get(
                    public_primary_key=attrs["alert_group_id"], channel__organization=organization
                )
            except ObjectDoesNotExist:
                raise serializers.ValidationError("Alert group {} does not exist".format(attrs["alert_group_id"]))

        return attrs
