import datetime

from django.utils import timezone
from rest_framework import serializers

from apps.schedules.ical_utils import list_users_to_notify_from_ical
from apps.slack.models import SlackUserGroup
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField
from common.api_helpers.exceptions import BadRequest


class ScheduleBaseSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    on_call_now = serializers.SerializerMethodField()
    slack = serializers.DictField(required=False)
    team_id = TeamPrimaryKeyRelatedField(required=False, allow_null=True, source="team")

    def create(self, validated_data):
        validated_data = self._correct_validated_data(validated_data)
        validated_data["organization"] = self.context["request"].auth.organization
        return super().create(validated_data)

    def get_on_call_now(self, obj):
        users_on_call = list_users_to_notify_from_ical(obj, datetime.datetime.now(timezone.utc))
        if users_on_call is not None:
            return [user.public_primary_key for user in users_on_call]
        else:
            return []

    def _correct_validated_data(self, validated_data):
        slack_field = validated_data.pop("slack", {})
        if "channel_id" in slack_field:
            validated_data["channel"] = slack_field["channel_id"]

        if "user_group_id" in slack_field:
            validated_data["user_group"] = SlackUserGroup.objects.filter(slack_id=slack_field["user_group_id"]).first()

        return validated_data

    def validate_slack(self, slack_field):
        from apps.slack.models import SlackChannel

        slack_channel_id = slack_field.get("channel_id")
        user_group_id = slack_field.get("user_group_id")

        organization = self.context["request"].auth.organization
        slack_team_identity = organization.slack_team_identity

        if slack_channel_id is not None:
            slack_channel_id = slack_channel_id.upper()
            try:
                slack_team_identity.get_cached_channels().get(slack_id=slack_channel_id)
            except SlackChannel.DoesNotExist:
                raise BadRequest(detail="Slack channel does not exist")

        if user_group_id is not None:
            user_group_id = user_group_id.upper()
            try:
                slack_team_identity.usergroups.get(slack_id=user_group_id)
            except SlackUserGroup.DoesNotExist:
                raise BadRequest(detail="Slack user group does not exist")

        return slack_field

    def to_representation(self, instance):
        result = super().to_representation(instance)

        user_group_id = instance.user_group.slack_id if instance.user_group is not None else None
        result["slack"] = {
            "channel_id": instance.channel or None,
            "user_group_id": user_group_id,
        }

        return result


class FinalShiftQueryParamsSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)

    def validate(self, attrs):
        if attrs["start_date"] > attrs["end_date"]:
            raise serializers.ValidationError("start_date must be less than or equal to end_date")
        if attrs["end_date"] - attrs["start_date"] > datetime.timedelta(days=365):
            raise serializers.ValidationError(
                "The difference between start_date and end_date must be less than one year (365 days)"
            )
        return attrs
