from rest_framework import serializers

from apps.schedules.models import CustomOnCallShift, OnCallScheduleWeb
from apps.user_management.models import User
from common.api_helpers.custom_fields import (
    OrganizationFilteredPrimaryKeyRelatedField,
    RollingUsersField,
    UsersFilteredByOrganizationField,
)
from common.api_helpers.mixins import EagerLoadingMixin
from common.api_helpers.utils import CurrentOrganizationDefault


class OnCallShiftSerializer(EagerLoadingMixin, serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    organization = serializers.HiddenField(default=CurrentOrganizationDefault())
    type = serializers.ChoiceField(
        required=True,
        choices=CustomOnCallShift.WEB_TYPES,
    )
    schedule = OrganizationFilteredPrimaryKeyRelatedField(queryset=OnCallScheduleWeb.objects)
    frequency = serializers.ChoiceField(required=False, choices=CustomOnCallShift.FREQUENCY_CHOICES, allow_null=True)
    shift_start = serializers.DateTimeField(source="start")
    shift_end = serializers.SerializerMethodField()
    by_day = serializers.ListField(required=False, allow_null=True)
    rolling_users = RollingUsersField(
        allow_null=True,
        required=False,
        child=UsersFilteredByOrganizationField(
            queryset=User.objects, required=False, allow_null=True
        ),  # todo: filter by team?
    )
    updated_shift = serializers.CharField(read_only=True, allow_null=True, source="updated_shift.public_primary_key")

    class Meta:
        model = CustomOnCallShift
        fields = [
            "id",
            "organization",
            "title",
            "type",
            "schedule",
            "priority_level",
            "shift_start",
            "shift_end",
            "rotation_start",
            "until",
            "frequency",
            "interval",
            "by_day",
            "source",
            "rolling_users",
            "updated_shift",
        ]
        extra_kwargs = {
            "interval": {"required": False, "allow_null": True},
            "source": {"required": False, "write_only": True},
        }

    SELECT_RELATED = ["schedule", "updated_shift"]

    def get_shift_end(self, obj):
        return obj.start + obj.duration

    def to_internal_value(self, data):
        data["source"] = CustomOnCallShift.SOURCE_WEB
        if not data.get("shift_end"):
            raise serializers.ValidationError({"shift_end": ["This field is required."]})

        result = super().to_internal_value(data)
        return result

    def validate_by_day(self, by_day):
        if by_day:
            for day in by_day:
                if day not in CustomOnCallShift.WEB_WEEKDAY_MAP:
                    raise serializers.ValidationError(["Invalid day value."])
        return by_day

    def validate_interval(self, interval):
        if interval is not None:
            if not isinstance(interval, int) or interval <= 0:
                raise serializers.ValidationError(["Invalid value"])
        return interval

    def validate_rolling_users(self, rolling_users):
        result = []
        if rolling_users:
            for users in rolling_users:
                users_dict = dict()
                for user in users:
                    users_dict[str(user.pk)] = user.public_primary_key
                result.append(users_dict)
        return result

    def _validate_shift_end(self, start, end):
        if end <= start:
            raise serializers.ValidationError({"shift_end": ["Incorrect shift end date"]})

    def _validate_frequency(self, frequency, event_type, rolling_users, interval, by_day, until):
        if frequency is None:
            if rolling_users and len(rolling_users) > 1:
                raise serializers.ValidationError(
                    {"rolling_users": ["Cannot set multiple user groups for non-recurrent shifts"]}
                )
            if interval is not None:
                raise serializers.ValidationError({"interval": ["Cannot set interval for non-recurrent shifts"]})
            if by_day:
                raise serializers.ValidationError({"by_day": ["Cannot set days value for non-recurrent shifts"]})
            if until:
                raise serializers.ValidationError({"until": ["Cannot set 'until' for non-recurrent shifts"]})
        else:
            if event_type == CustomOnCallShift.TYPE_OVERRIDE:
                raise serializers.ValidationError(
                    {"frequency": ["Cannot set 'frequency' for shifts with type 'override'"]}
                )
            if frequency not in (CustomOnCallShift.FREQUENCY_WEEKLY, CustomOnCallShift.FREQUENCY_DAILY) and by_day:
                raise serializers.ValidationError({"by_day": ["Cannot set days value for this frequency type"]})
            if frequency == CustomOnCallShift.FREQUENCY_DAILY and by_day and interval > len(by_day):
                raise serializers.ValidationError(
                    {"interval": ["Interval must be less than or equal to the number of selected days"]}
                )

    def _validate_rotation_start(self, shift_start, rotation_start):
        if rotation_start < shift_start:
            raise serializers.ValidationError({"rotation_start": ["Incorrect rotation start date"]})

    def _validate_until(self, rotation_start, until):
        if until is not None and until < rotation_start:
            raise serializers.ValidationError({"until": ["Incorrect rotation end date"]})

    def _correct_validated_data(self, event_type, validated_data):
        fields_to_update_for_overrides = [
            "priority_level",
            "rotation_start",
        ]
        if event_type == CustomOnCallShift.TYPE_OVERRIDE:
            for field in fields_to_update_for_overrides:
                value = None
                if field == "priority_level":
                    value = 0
                elif field == "rotation_start":
                    value = validated_data["start"]
                validated_data[field] = value

        self._validate_frequency(
            validated_data.get("frequency"),
            event_type,
            validated_data.get("rolling_users"),
            validated_data.get("interval"),
            validated_data.get("by_day"),
            validated_data.get("until"),
        )
        self._validate_rotation_start(validated_data["start"], validated_data["rotation_start"])
        self._validate_until(validated_data["rotation_start"], validated_data.get("until"))

        # convert shift_end into internal value and validate
        raw_shift_end = self.initial_data["shift_end"]
        shift_end = serializers.DateTimeField().to_internal_value(raw_shift_end)
        self._validate_shift_end(validated_data["start"], shift_end)

        validated_data["duration"] = shift_end - validated_data["start"]
        if validated_data.get("schedule"):
            validated_data["team"] = validated_data["schedule"].team

        validated_data["week_start"] = CustomOnCallShift.MONDAY

        return validated_data

    def create(self, validated_data):
        validated_data = self._correct_validated_data(validated_data["type"], validated_data)
        validated_data["name"] = CustomOnCallShift.generate_name(
            validated_data["schedule"], validated_data["priority_level"], validated_data["type"]
        )
        instance = super().create(validated_data)

        instance.start_drop_ical_and_check_schedule_tasks(instance.schedule)
        return instance


class OnCallShiftUpdateSerializer(OnCallShiftSerializer):
    schedule = serializers.CharField(read_only=True, source="schedule.public_primary_key")
    type = serializers.ReadOnlyField()

    class Meta(OnCallShiftSerializer.Meta):
        read_only_fields = ("schedule", "type")

    def update(self, instance, validated_data):
        validated_data = self._correct_validated_data(instance.type, validated_data)
        change_only_title = True
        create_or_update_last_shift = False

        for field in validated_data:
            if field != "title" and validated_data[field] != getattr(instance, field):
                change_only_title = False
                break

        if not change_only_title:
            if instance.type != CustomOnCallShift.TYPE_OVERRIDE:
                if instance.event_is_started:
                    create_or_update_last_shift = True

            elif instance.event_is_finished:
                raise serializers.ValidationError(["This event cannot be updated"])

        if create_or_update_last_shift:
            result = instance.create_or_update_last_shift(validated_data)
        else:
            result = super().update(instance, validated_data)

        instance.start_drop_ical_and_check_schedule_tasks(instance.schedule)
        return result
