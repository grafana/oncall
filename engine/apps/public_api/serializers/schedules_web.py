from apps.public_api.serializers.schedules_base import ScheduleBaseSerializer
from apps.schedules.models import CustomOnCallShift, OnCallScheduleWeb
from apps.schedules.tasks import (
    drop_cached_ical_task,
    schedule_notify_about_empty_shifts_in_schedule,
    schedule_notify_about_gaps_in_schedule,
)
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField, TimeZoneField, UsersFilteredByOrganizationField


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
