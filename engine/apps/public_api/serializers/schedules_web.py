from apps.public_api.serializers.schedules_base import ScheduleBaseSerializer
from apps.schedules.models import CustomOnCallShift, OnCallScheduleWeb
from apps.schedules.tasks import (
    drop_cached_ical_task,
    schedule_notify_about_empty_shifts_in_schedule,
    schedule_notify_about_gaps_in_schedule,
)
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField, UsersFilteredByOrganizationField
from common.api_helpers.exceptions import BadRequest
from common.timezones import TimeZoneField


class ScheduleWebSerializer(ScheduleBaseSerializer):
    team_id = TeamPrimaryKeyRelatedField(required=False, allow_null=True, source="team")
    time_zone = TimeZoneField(required=True)
    shifts = UsersFilteredByOrganizationField(
        queryset=CustomOnCallShift.objects,
        required=False,
        source="custom_shifts",
    )

    class Meta:
        model = OnCallScheduleWeb
        fields = [
            "id",
            "team_id",
            "name",
            "time_zone",
            "slack",
            "on_call_now",
            "shifts",
        ]

    def validate_shifts(self, shifts):
        # Get team_id from instance, if it exists, otherwise get it from initial data.
        # Handle empty string instead of None. In this case change team_id value to None.
        team_id = self.instance.team_id if self.instance else (self.initial_data.get("team_id") or None)
        for shift in shifts:
            if shift.team_id != team_id:
                raise BadRequest(detail="Shifts must be assigned to the same team as the schedule")

        return shifts

    def to_internal_value(self, data):
        if data.get("shifts", []) is None:  # handle a None value
            data["shifts"] = []
        result = super().to_internal_value(data)
        return result


class ScheduleWebUpdateSerializer(ScheduleWebSerializer):
    time_zone = TimeZoneField(required=False)

    class Meta:
        model = OnCallScheduleWeb
        fields = [
            "id",
            "team_id",
            "name",
            "time_zone",
            "slack",
            "on_call_now",
            "shifts",
        ]
        extra_kwargs = {
            "name": {"required": False},
        }

    def update(self, instance, validated_data):
        validated_data = self._correct_validated_data(validated_data)
        new_time_zone = validated_data.get("time_zone", instance.time_zone)
        new_shifts = validated_data.get("shifts", [])
        existing_shifts = instance.custom_shifts.all()

        ical_changed = False

        if new_time_zone != instance.time_zone or set(existing_shifts) != set(new_shifts):
            ical_changed = True

        if ical_changed:
            drop_cached_ical_task.apply_async(
                (instance.pk,),
            )
            schedule_notify_about_empty_shifts_in_schedule.apply_async((instance.pk,))
            schedule_notify_about_gaps_in_schedule.apply_async((instance.pk,))
        return super().update(instance, validated_data)
