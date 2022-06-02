import pytz
from django.utils import timezone
from rest_framework import serializers

from apps.public_api.serializers.schedules_base import ScheduleBaseSerializer
from apps.schedules.models import CustomOnCallShift, OnCallScheduleCalendar
from apps.schedules.tasks import (
    drop_cached_ical_task,
    schedule_notify_about_empty_shifts_in_schedule,
    schedule_notify_about_gaps_in_schedule,
)
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField, UsersFilteredByOrganizationField
from common.api_helpers.exceptions import BadRequest


class ScheduleCalendarSerializer(ScheduleBaseSerializer):
    time_zone = serializers.CharField(required=True)
    shifts = UsersFilteredByOrganizationField(
        queryset=CustomOnCallShift.objects,
        required=False,
        source="custom_on_call_shifts",
    )

    class Meta:
        model = OnCallScheduleCalendar
        fields = [
            "id",
            "team_id",
            "name",
            "time_zone",
            "slack",
            "on_call_now",
            "shifts",
            "ical_url_overrides",
        ]
        extra_kwargs = {
            "ical_url_overrides": {"required": False, "allow_null": True},
        }

    def validate_time_zone(self, tz):
        try:
            timezone.now().astimezone(pytz.timezone(tz))
        except pytz.exceptions.UnknownTimeZoneError:
            raise BadRequest(detail="Invalid time zone")
        return tz

    def validate_shifts(self, shifts):
        # Get team_id from instance, if it exists, otherwise get it from initial data.
        # Terraform sends empty string instead of None. In this case change team_id value to None.
        team_id = self.instance.team_id if self.instance else (self.initial_data.get("team_id") or None)
        for shift in shifts:
            if shift.team_id != team_id:
                raise BadRequest(detail="Shifts must be assigned to the same team as the schedule")

        return shifts

    def to_internal_value(self, data):
        if data.get("shifts", []) is None:  # terraform case
            data["shifts"] = []
        result = super().to_internal_value(data)
        return result


class ScheduleCalendarUpdateSerializer(ScheduleCalendarSerializer):
    time_zone = serializers.CharField(required=False)
    team_id = TeamPrimaryKeyRelatedField(read_only=True, source="team")

    class Meta:
        model = OnCallScheduleCalendar
        fields = [
            "id",
            "team_id",
            "name",
            "time_zone",
            "slack",
            "on_call_now",
            "shifts",
            "ical_url_overrides",
        ]
        extra_kwargs = {
            "name": {"required": False},
            "ical_url_overrides": {"required": False, "allow_null": True},
        }

    def update(self, instance, validated_data):
        validated_data = self._correct_validated_data(validated_data)
        new_time_zone = validated_data.get("time_zone", instance.time_zone)
        new_shifts = validated_data.get("shifts", [])
        existing_shifts = instance.custom_on_call_shifts.all()

        ical_changed = False

        if new_time_zone != instance.time_zone or set(existing_shifts) != set(new_shifts):
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
        return super().update(instance, validated_data)
