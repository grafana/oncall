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

    class Meta:
        model = CustomOnCallShift
        fields = [
            "id",
            "organization",
            "name",
            "type",
            "schedule",
            "priority_level",
            "shift_start",
            "shift_end",
            "rotation_start",
            "until",
            "frequency",
            "interval",
            "until",
            "by_day",
            "source",
            "rolling_users",
        ]
        extra_kwargs = {
            "interval": {"required": False, "allow_null": True},
            "source": {"required": False, "write_only": True},
        }

    SELECT_RELATED = ["schedule"]

    def get_shift_end(self, obj):
        return obj.start + obj.duration

    def to_internal_value(self, data):
        data["source"] = CustomOnCallShift.SOURCE_WEB
        data["week_start"] = CustomOnCallShift.MONDAY
        if not data.get("shift_end"):
            raise serializers.ValidationError({"shift_end": ["This field is required."]})

        result = super().to_internal_value(data)
        return result

    def to_representation(self, instance):
        result = super().to_representation(instance)
        return result

    def validate_name(self, name):  # todo
        organization = self.context["request"].auth.organization
        if name is None:
            return name
        try:
            obj = CustomOnCallShift.objects.get(organization=organization, name=name)
        except CustomOnCallShift.DoesNotExist:
            return name
        if self.instance and obj.id == self.instance.id:
            return name
        else:
            raise serializers.ValidationError(["On-call shift with this name already exists"])

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
                    users_dict[user.pk] = user.public_primary_key
                result.append(users_dict)
        return result

    def _validate_shift_end(self, start, end):
        if end <= start:
            raise serializers.ValidationError({"shift_end": ["Incorrect shift end date"]})

    def _validate_frequency(self, frequency, event_type, rolling_users, interval, by_day):
        if frequency is None:
            if rolling_users and len(rolling_users) > 1:
                raise serializers.ValidationError(
                    {"rolling_users": ["Cannot set multiple user groups for non-recurrent shifts"]}
                )
            if interval is not None:
                raise serializers.ValidationError({"interval": ["Cannot set interval for non-recurrent shifts"]})
            if by_day:
                raise serializers.ValidationError({"by_day": ["Cannot set days value for non-recurrent shifts"]})
        else:
            if event_type == CustomOnCallShift.TYPE_OVERRIDE:
                raise serializers.ValidationError(
                    {"frequency": ["Cannot set 'frequency' for shifts with type 'override'"]}
                )
            if frequency != CustomOnCallShift.FREQUENCY_WEEKLY and by_day:
                raise serializers.ValidationError({"by_day": ["Cannot set days value for this frequency type"]})

    def _validate_rotation_start(self, shift_start, rotation_start):
        if rotation_start < shift_start:
            raise serializers.ValidationError({"rotation_start": ["Incorrect rotation start date"]})

    def _validate_until(self, rotation_start, until):
        if until is not None and until < rotation_start:
            raise serializers.ValidationError({"until": ["Incorrect rotation end date"]})

    def _correct_validated_data(self, event_type, validated_data):
        fields_to_update_for_overrides = [
            "priority_level",
            "frequency",
            "interval",
            "by_day",
            "until",
        ]
        if event_type == CustomOnCallShift.TYPE_OVERRIDE:
            for field in fields_to_update_for_overrides:
                value = None
                if field == "priority_level":
                    value = 0
                validated_data[field] = value

        self._validate_frequency(
            validated_data.get("frequency"),
            event_type,
            validated_data.get("rolling_users"),
            validated_data.get("interval"),
            validated_data.get("by_day"),
        )
        self._validate_rotation_start(validated_data["start"], validated_data["rotation_start"])
        self._validate_until(validated_data["rotation_start"], validated_data.get("until"))

        # convert shift_end into internal value and validate
        raw_shift_end = self.initial_data["shift_end"]
        shift_end = serializers.DateTimeField().to_internal_value(raw_shift_end)
        self._validate_shift_end(validated_data["start"], shift_end)

        validated_data["duration"] = shift_end - validated_data["start"]
        validated_data["team"] = validated_data["schedule"].team

        return validated_data

    def create(self, validated_data):
        validated_data = self._correct_validated_data(validated_data["type"], validated_data)

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

        result = super().update(instance, validated_data)

        instance.start_drop_ical_and_check_schedule_tasks(instance.schedule)
        return result
