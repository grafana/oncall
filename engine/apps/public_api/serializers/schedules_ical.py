from apps.public_api.serializers.schedules_base import ScheduleBaseSerializer
from apps.schedules.models import OnCallScheduleICal
from apps.schedules.tasks import (
    drop_cached_ical_task,
    refresh_ical_final_schedule,
    schedule_notify_about_empty_shifts_in_schedule,
    schedule_notify_about_gaps_in_schedule,
)
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField
from common.api_helpers.utils import validate_ical_url


class ScheduleICalSerializer(ScheduleBaseSerializer):
    class Meta:
        model = OnCallScheduleICal
        fields = [
            "id",
            "team_id",
            "name",
            "ical_url_primary",
            "ical_url_overrides",
            "slack",
            "on_call_now",
        ]
        extra_kwargs = {
            "ical_url_primary": {"required": True, "allow_null": False},
            "ical_url_overrides": {"required": False, "allow_null": True},
        }

    def validate_ical_url_primary(self, url):
        return validate_ical_url(url)

    def validate_ical_url_overrides(self, url):
        return validate_ical_url(url)

    def create(self, validated_data):
        created_schedule = super().create(validated_data)
        # for iCal-based schedules we need to refresh final schedule information
        refresh_ical_final_schedule.apply_async((created_schedule.pk,))
        return created_schedule


class ScheduleICalUpdateSerializer(ScheduleICalSerializer):
    team_id = TeamPrimaryKeyRelatedField(required=False, allow_null=True, source="team")

    class Meta:
        model = OnCallScheduleICal
        fields = [
            "id",
            "team_id",
            "name",
            "ical_url_primary",
            "ical_url_overrides",
            "slack",
            "on_call_now",
        ]
        extra_kwargs = {
            "name": {"required": False},
            "ical_url_primary": {"required": False, "allow_null": False},
            "ical_url_overrides": {"required": False, "allow_null": True},
        }

    def update(self, instance, validated_data):
        ical_changed = False
        validated_data = self._correct_validated_data(validated_data)

        if "ical_url_primary" in validated_data and validated_data["ical_url_primary"] != instance.ical_url_primary:
            ical_changed = True
        if (
            "ical_url_overrides" in validated_data
            and validated_data["ical_url_overrides"] != instance.ical_url_overrides
        ):
            ical_changed = True
        if ical_changed:
            drop_cached_ical_task.apply_async(
                (instance.pk,),
            )
            schedule_notify_about_empty_shifts_in_schedule.apply_async((instance.pk,))
            schedule_notify_about_gaps_in_schedule.apply_async((instance.pk,))
            refresh_ical_final_schedule.apply_async((instance.pk,))
        return super().update(instance, validated_data)
