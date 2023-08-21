from rest_framework import serializers

from apps.api.serializers.schedule_base import ScheduleBaseSerializer
from apps.schedules.models import OnCallScheduleCalendar
from apps.schedules.tasks import schedule_notify_about_empty_shifts_in_schedule, schedule_notify_about_gaps_in_schedule
from apps.slack.models import SlackChannel, SlackUserGroup
from common.api_helpers.custom_fields import OrganizationFilteredPrimaryKeyRelatedField, TimeZoneField
from common.api_helpers.utils import validate_ical_url


class ScheduleCalendarSerializer(ScheduleBaseSerializer):
    time_zone = TimeZoneField(required=False)
    enable_web_overrides = serializers.BooleanField(required=False, allow_null=True)

    class Meta:
        model = OnCallScheduleCalendar
        fields = [*ScheduleBaseSerializer.Meta.fields, "slack_channel", "time_zone", "ical_url_overrides"]

    def validate_ical_url_overrides(self, url):
        return validate_ical_url(url)


class ScheduleCalendarCreateSerializer(ScheduleCalendarSerializer):
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

    class Meta(ScheduleCalendarSerializer.Meta):
        fields = [*ScheduleBaseSerializer.Meta.fields, "slack_channel_id", "time_zone", "ical_url_overrides"]
        extra_kwargs = {
            "ical_url_overrides": {"required": False, "allow_null": True},
        }

    def update(self, instance, validated_data):
        old_ical_url_overrides = instance.ical_url_overrides
        old_time_zone = instance.time_zone
        old_enable_web_overrides = instance.enable_web_overrides

        updated_schedule = super().update(instance, validated_data)

        updated_ical_url_overrides = updated_schedule.ical_url_overrides
        updated_time_zone = updated_schedule.time_zone
        updated_enable_web_overrides = updated_schedule.enable_web_overrides

        if (
            old_time_zone != updated_time_zone
            or old_ical_url_overrides != updated_ical_url_overrides
            or old_enable_web_overrides != updated_enable_web_overrides
        ):
            updated_schedule.drop_cached_ical()
            updated_schedule.check_empty_shifts_for_next_week()
            updated_schedule.check_gaps_for_next_week()
            schedule_notify_about_empty_shifts_in_schedule.apply_async((instance.pk,))
            schedule_notify_about_gaps_in_schedule.apply_async((instance.pk,))
        return updated_schedule
