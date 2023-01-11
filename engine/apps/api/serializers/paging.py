from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from apps.alerts.models import AlertGroup


def get_user(organization, user_id):
    try:
        return organization.users.get(public_primary_key=user_id)
    except ObjectDoesNotExist:
        raise serializers.ValidationError("User {} does not exist".format(user_id))


def get_schedule(organization, schedule_id):
    try:
        return organization.schedules.get(public_primary_key=schedule_id)
    except ObjectDoesNotExist:
        raise serializers.ValidationError("Schedule {} does not exist".format(schedule_id))


def get_alert_group(organization, alert_group_id):
    try:
        return AlertGroup.unarchived_objects.get(public_primary_key=alert_group_id, channel__organization=organization)
    except ObjectDoesNotExist:
        raise serializers.ValidationError("Alert group {} does not exist".format(alert_group_id))


class CheckUserAvailabilitySerializer(serializers.Serializer):
    user_id = serializers.CharField()
    user = serializers.HiddenField(default=None)  # set in CheckUserAvailabilitySerializer.validate

    def validate(self, attrs):
        organization = self.context["organization"]
        attrs["user"] = get_user(organization, attrs["user_id"])
        return attrs


class UserReferenceSerializer(serializers.Serializer):
    id = serializers.CharField()
    important = serializers.BooleanField()
    instance = serializers.HiddenField(default=None)  # set in UserReferenceSerializer.validate

    def validate(self, attrs):
        organization = self.context["organization"]
        attrs["instance"] = get_user(organization, attrs["id"])
        return attrs


class ScheduleReferenceSerializer(serializers.Serializer):
    id = serializers.CharField()
    important = serializers.BooleanField()
    instance = serializers.HiddenField(default=None)  # set in ScheduleReferenceSerializer.validate

    def validate(self, attrs):
        organization = self.context["organization"]
        attrs["instance"] = get_schedule(organization, attrs["id"])
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

        if not attrs["alert_group_id"] and not attrs["title"]:
            raise serializers.ValidationError("Provide either alert_group_id or title")

        if attrs["alert_group_id"] and (attrs["title"] or attrs["message"]):
            raise serializers.ValidationError("alert_group_id and (title, message) are mutually exclusive")

        if attrs["alert_group_id"]:
            organization = self.context["organization"]
            attrs["alert_group"] = get_alert_group(organization, attrs["alert_group_id"])

        return attrs


class UnpageUserSerializer(serializers.Serializer):
    alert_group_id = serializers.CharField()
    user_id = serializers.CharField()

    alert_group = serializers.HiddenField(default=None)  # set in UnpageUserSerializer.validate
    user = serializers.HiddenField(default=None)  # set in UnpageUserSerializer.validate

    def validate(self, attrs):
        organization = self.context["organization"]

        attrs["alert_group"] = get_alert_group(organization, attrs["alert_group_id"])
        attrs["user"] = get_user(organization, attrs["user_id"])

        return attrs
