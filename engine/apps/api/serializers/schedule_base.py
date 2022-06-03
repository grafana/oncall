from django.utils import timezone
from rest_framework import serializers

from apps.api.serializers.user_group import UserGroupSerializer
from apps.schedules.ical_utils import list_users_to_notify_from_ical
from apps.schedules.tasks import schedule_notify_about_empty_shifts_in_schedule, schedule_notify_about_gaps_in_schedule
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField
from common.api_helpers.mixins import EagerLoadingMixin
from common.api_helpers.utils import CurrentOrganizationDefault, CurrentTeamDefault


class ScheduleBaseSerializer(EagerLoadingMixin, serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    organization = serializers.HiddenField(default=CurrentOrganizationDefault())
    team = TeamPrimaryKeyRelatedField(allow_null=True, default=CurrentTeamDefault())
    slack_channel = serializers.SerializerMethodField()
    user_group = UserGroupSerializer()
    warnings = serializers.SerializerMethodField()
    on_call_now = serializers.SerializerMethodField()

    class Meta:
        fields = [
            "id",
            "organization",
            "team",
            "name",
            "user_group",
            "warnings",
            "on_call_now",
            "has_gaps",
            "notify_oncall_shift_freq",
            "notify_empty_oncall",
            "mention_oncall_start",
            "mention_oncall_next",
        ]

    SELECT_RELATED = ["organization"]

    CANT_UPDATE_USER_GROUP_WARNING = (
        "Cannot update the user group, make sure to grant user group modification rights to "
        "non-admin users in Slack workspace settings"
    )
    SCHEDULE_HAS_GAPS_WARNING = "Schedule has unassigned time periods during next 7 days"
    SCHEDULE_HAS_EMPTY_SHIFTS_WARNING = "Schedule has empty shifts during next 7 days"

    def get_slack_channel(self, obj):
        if obj.channel is None:
            return None
        return {
            "display_name": obj.slack_channel_name,
            "slack_id": obj.channel,
            "id": obj.slack_channel_pk,
        }

    def get_warnings(self, obj):
        can_update_user_groups = self.context.get("can_update_user_groups", False)
        warnings = []
        if obj.user_group and not can_update_user_groups:
            warnings.append(self.CANT_UPDATE_USER_GROUP_WARNING)
        if obj.has_gaps:
            warnings.append(self.SCHEDULE_HAS_GAPS_WARNING)
        if obj.has_empty_shifts:
            warnings.append(self.SCHEDULE_HAS_EMPTY_SHIFTS_WARNING)
        return warnings

    def get_on_call_now(self, obj):
        users_on_call = list_users_to_notify_from_ical(obj, timezone.datetime.now(timezone.utc))
        if users_on_call is not None:
            return [user.short() for user in users_on_call]
        else:
            return []

    def validate(self, attrs):
        if "slack_channel_id" in attrs:
            slack_channel_id = attrs.pop("slack_channel_id", None)
            attrs["channel"] = slack_channel_id.slack_id if slack_channel_id is not None else None
        return attrs

    def create(self, validated_data):
        created_schedule = super().create(validated_data)
        created_schedule.check_empty_shifts_for_next_week()
        schedule_notify_about_empty_shifts_in_schedule.apply_async((created_schedule.pk,))
        created_schedule.check_gaps_for_next_week()
        schedule_notify_about_gaps_in_schedule.apply_async((created_schedule.pk,))
        return created_schedule
