from apps.api.serializers.schedule_base import ScheduleBaseSerializer
from apps.schedules.models import OnCallScheduleICal
from apps.schedules.tasks import schedule_notify_about_empty_shifts_in_schedule, schedule_notify_about_gaps_in_schedule
from apps.slack.models import SlackChannel, SlackUserGroup
from common.api_helpers.custom_fields import OrganizationFilteredPrimaryKeyRelatedField
from common.api_helpers.utils import validate_ical_url


class ScheduleICalSerializer(ScheduleBaseSerializer):
    class Meta:
        model = OnCallScheduleICal
        fields = [
            *ScheduleBaseSerializer.Meta.fields,
            "ical_url_primary",
            "ical_url_overrides",
            "slack_channel",
        ]

    def validate_ical_url_primary(self, url):
        return validate_ical_url(url)

    def validate_ical_url_overrides(self, url):
        return validate_ical_url(url)


class ScheduleICalCreateSerializer(ScheduleICalSerializer):
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

    class Meta:
        model = OnCallScheduleICal
        fields = [
            *ScheduleBaseSerializer.Meta.fields,
            "ical_url_primary",
            "ical_url_overrides",
            "slack_channel_id",
        ]
        extra_kwargs = {
            "ical_url_primary": {"required": True, "allow_null": False},
            "ical_url_overrides": {"required": False, "allow_null": True},
        }


class ScheduleICalUpdateSerializer(ScheduleICalCreateSerializer):
    class Meta:
        model = OnCallScheduleICal
        fields = [
            *ScheduleBaseSerializer.Meta.fields,
            "ical_url_primary",
            "ical_url_overrides",
            "slack_channel_id",
        ]
        extra_kwargs = {
            "ical_url_primary": {"required": False, "allow_null": False},
            "ical_url_overrides": {"required": False, "allow_null": True},
        }

    def update(self, instance, validated_data):
        old_ical_url_primary = instance.ical_url_primary
        old_ical_url_overrides = instance.ical_url_overrides

        updated_schedule = super().update(instance, validated_data)

        updated_ical_url_primary = updated_schedule.ical_url_primary
        updated_ical_url_overrides = updated_schedule.ical_url_overrides

        if old_ical_url_primary != updated_ical_url_primary or old_ical_url_overrides != updated_ical_url_overrides:
            updated_schedule.drop_cached_ical()
            updated_schedule.check_empty_shifts_for_next_week()
            updated_schedule.check_gaps_for_next_week()
            schedule_notify_about_empty_shifts_in_schedule.apply_async((instance.pk,))
            schedule_notify_about_gaps_in_schedule.apply_async((instance.pk,))
        return updated_schedule
