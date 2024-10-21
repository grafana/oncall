import datetime
import typing

from rest_framework import serializers

from apps.schedules.ical_utils import list_users_to_notify_from_ical
from apps.slack.models import SlackChannel, SlackUserGroup
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import EagerLoadingMixin

if typing.TYPE_CHECKING:
    from apps.schedules.models import OnCallSchedule
    from apps.user_management.models import Organization


class ScheduleBaseSerializer(EagerLoadingMixin, serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    on_call_now = serializers.SerializerMethodField()
    slack = serializers.DictField(required=False)
    team_id = TeamPrimaryKeyRelatedField(required=False, allow_null=True, source="team")

    SELECT_RELATED = ["team", "user_group", "slack_channel"]

    def create(self, validated_data):
        organization = self.context["request"].auth.organization

        validated_data = self._correct_validated_data(validated_data, organization)
        validated_data["organization"] = organization
        return super().create(validated_data)

    def get_on_call_now(self, obj: "OnCallSchedule") -> typing.List[str]:
        users_on_call = list_users_to_notify_from_ical(obj, datetime.datetime.now(datetime.timezone.utc))
        if users_on_call is not None:
            return [user.public_primary_key for user in users_on_call]
        else:
            return []

    def _correct_validated_data(self, validated_data, organization: "Organization"):
        slack_field = validated_data.pop("slack", {})
        slack_team_identity = organization.slack_team_identity

        if not slack_team_identity:
            raise BadRequest("Slack isn't connected to this workspace")

        if "channel_id" in slack_field:
            validated_data["slack_channel"] = SlackChannel.objects.get(
                slack_team_identity=slack_team_identity,
                slack_id=slack_field["channel_id"],
            )

        if "user_group_id" in slack_field:
            validated_data["user_group"] = SlackUserGroup.objects.get(
                slack_team_identity=slack_team_identity,
                slack_id=slack_field["user_group_id"],
            )

        return validated_data

    def validate_slack(self, slack_field):
        slack_channel_id = slack_field.get("channel_id")
        user_group_id = slack_field.get("user_group_id")

        organization = self.context["request"].auth.organization
        slack_team_identity = organization.slack_team_identity

        if (slack_channel_id or user_group_id) and not slack_team_identity:
            raise BadRequest(detail="Slack isn't connected to this workspace")

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

    def to_representation(self, instance: "OnCallSchedule"):
        return {
            **super().to_representation(instance),
            "slack": {
                "channel_id": instance.slack_channel_slack_id,
                "user_group_id": instance.user_group.slack_id if instance.user_group is not None else None,
            },
        }


class FinalShiftQueryParamsSerializer(serializers.Serializer):
    start_date = serializers.DateTimeField(required=True, input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d"])
    end_date = serializers.DateTimeField(required=True, input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d"])

    def validate(self, attrs):
        if attrs["start_date"] > attrs["end_date"]:
            raise serializers.ValidationError("start_date must be less than or equal to end_date")
        if attrs["end_date"] - attrs["start_date"] > datetime.timedelta(days=365):
            raise serializers.ValidationError(
                "The difference between start_date and end_date must be less than one year (365 days)"
            )
        return attrs
