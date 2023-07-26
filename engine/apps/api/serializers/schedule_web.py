from apps.api.serializers.schedule_base import ScheduleBaseSerializer
from apps.schedules.models import OnCallScheduleWeb
from apps.schedules.tasks import schedule_notify_about_empty_shifts_in_schedule, schedule_notify_about_gaps_in_schedule
from apps.slack.models import SlackChannel, SlackUserGroup
from common.api_helpers.custom_fields import OrganizationFilteredPrimaryKeyRelatedField, TimeZoneField


class ScheduleWebSerializer(ScheduleBaseSerializer):
    time_zone = TimeZoneField(required=False)

    class Meta:
        model = OnCallScheduleWeb
        fields = [*ScheduleBaseSerializer.Meta.fields, "slack_channel", "time_zone"]

    def get_enable_web_overrides(self, obj):
        return True


class ScheduleWebCreateSerializer(ScheduleWebSerializer):
    slack_channel_id = OrganizationFilteredPrimaryKeyRelatedField(
        filter_field="slack_team_identity__organizations",
        queryset=SlackChannel.objects,
        required=False,
        allow_null=True,
    )
    user_group = OrganizationFilteredPrimaryKeyRelatedField(
        filter_field="slack_team_identity__organizations",
        queryset=SlackUserGroup.objects,
        required=False,
        allow_null=True,
    )

    class Meta(ScheduleWebSerializer.Meta):
        fields = [*ScheduleBaseSerializer.Meta.fields, "slack_channel_id", "time_zone"]

    def update(self, instance, validated_data):
        updated_schedule = super().update(instance, validated_data)

        old_time_zone = instance.time_zone
        updated_time_zone = updated_schedule.time_zone
        if old_time_zone != updated_time_zone:
            updated_schedule.drop_cached_ical()
            updated_schedule.check_empty_shifts_for_next_week()
            updated_schedule.check_gaps_for_next_week()
            schedule_notify_about_empty_shifts_in_schedule.apply_async((instance.pk,))
            schedule_notify_about_gaps_in_schedule.apply_async((instance.pk,))
        return updated_schedule
