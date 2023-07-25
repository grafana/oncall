import time

from rest_framework import fields, serializers

from apps.schedules.models import CustomOnCallShift
from apps.user_management.models import User
from common.api_helpers.custom_fields import (
    RollingUsersField,
    TeamPrimaryKeyRelatedField,
    TimeZoneField,
    UsersFilteredByOrganizationField,
)
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import EagerLoadingMixin
from common.api_helpers.utils import CurrentOrganizationDefault


class CustomOnCallShiftTypeField(fields.CharField):
    def to_representation(self, value):
        return CustomOnCallShift.PUBLIC_TYPE_CHOICES_MAP[value]

    def to_internal_value(self, data):
        try:
            shift_type = [
                key
                for key, value in CustomOnCallShift.PUBLIC_TYPE_CHOICES_MAP.items()
                if value == data and key in CustomOnCallShift.PUBLIC_TYPE_CHOICES_MAP
            ][0]
        except IndexError:
            raise BadRequest(detail="Invalid shift type")
        return shift_type


class CustomOnCallShiftWeekStartField(fields.CharField):
    def to_representation(self, value):
        return CustomOnCallShift.ICAL_WEEKDAY_MAP[value]

    def to_internal_value(self, data):
        try:
            week_start = [
                key
                for key, value in CustomOnCallShift.ICAL_WEEKDAY_MAP.items()
                if value == data and key in CustomOnCallShift.ICAL_WEEKDAY_MAP
            ][0]
        except IndexError:
            raise BadRequest(
                detail="Invalid day format for week start field. "
                "Should be one of the following: 'MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU'"
            )
        return week_start


class CustomOnCallShiftFrequencyField(fields.CharField):
    def to_representation(self, value):
        return CustomOnCallShift.PUBLIC_FREQUENCY_CHOICES_MAP[value]

    def to_internal_value(self, data):
        try:
            frequency = [
                key
                for key, value in CustomOnCallShift.PUBLIC_FREQUENCY_CHOICES_MAP.items()
                if value == data and key in CustomOnCallShift.PUBLIC_FREQUENCY_CHOICES_MAP
            ][0]
        except IndexError:
            raise BadRequest(detail="Invalid frequency type")
        return frequency


class CustomOnCallShiftSerializer(EagerLoadingMixin, serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    organization = serializers.HiddenField(default=CurrentOrganizationDefault())
    team_id = TeamPrimaryKeyRelatedField(required=False, allow_null=True, source="team")
    type = CustomOnCallShiftTypeField()
    time_zone = TimeZoneField(required=False, allow_null=True)
    users = UsersFilteredByOrganizationField(queryset=User.objects, required=False)
    frequency = CustomOnCallShiftFrequencyField(required=False, allow_null=True)
    week_start = CustomOnCallShiftWeekStartField(required=False)
    level = serializers.IntegerField(required=False, source="priority_level")
    by_day = serializers.ListField(required=False, allow_null=True)
    by_month = serializers.ListField(required=False, allow_null=True)
    by_monthday = serializers.ListField(required=False, allow_null=True)
    rolling_users = RollingUsersField(
        allow_null=True,
        required=False,
        child=UsersFilteredByOrganizationField(queryset=User.objects, required=False, allow_null=True),
    )
    rotation_start = serializers.DateTimeField(required=False)

    class Meta:
        model = CustomOnCallShift
        fields = [
            "id",
            "organization",
            "team_id",
            "name",
            "type",
            "time_zone",
            "level",
            "start",
            "duration",
            "rotation_start",
            "frequency",
            "interval",
            "until",
            "week_start",
            "by_day",
            "by_month",
            "by_monthday",
            "source",
            "users",
            "rolling_users",
            "start_rotation_from_user_index",
        ]
        extra_kwargs = {
            "interval": {"required": False, "allow_null": True},
            "source": {"required": False, "write_only": True},
        }

    PREFETCH_RELATED = ["users"]

    def create(self, validated_data):
        self._validate_frequency_and_week_start(
            validated_data["type"],
            validated_data.get("frequency"),
            validated_data.get("interval", 1),  # if field is missing, the default value will be used
            validated_data.get("week_start"),
        )
        validated_data = self._correct_validated_data(validated_data["type"], validated_data)
        self._validate_start_rotation_from_user_index(
            validated_data["type"],
            validated_data.get("start_rotation_from_user_index"),
        )
        self._validate_frequency_daily(
            validated_data["type"],
            validated_data.get("frequency"),
            validated_data.get("interval"),
            validated_data.get("by_day"),
            validated_data.get("by_monthday"),
        )
        if not validated_data.get("rotation_start"):
            validated_data["rotation_start"] = validated_data["start"]
        instance = super().create(validated_data)
        for schedule in instance.schedules.all():
            instance.start_drop_ical_and_check_schedule_tasks(schedule)
        return instance

    def validate_by_day(self, by_day):
        if by_day:
            for day in by_day:
                if day not in CustomOnCallShift.ICAL_WEEKDAY_MAP.values():
                    raise BadRequest(
                        detail="Invalid day value in by_day field. "
                        "Valid values: 'MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU'"
                    )
        return by_day

    def validate_by_month(self, by_month):
        if by_month:
            for month in by_month:
                if not isinstance(month, int) or not 1 <= month <= 12:
                    raise BadRequest(detail="Invalid month value in by_month field. Valid values: from 1 to 12")
        return by_month

    def validate_by_monthday(self, by_monthday):
        if by_monthday:
            for day in by_monthday:
                if not isinstance(day, int) or not -31 <= day <= 31 or day == 0:
                    raise BadRequest(
                        detail="Invalid monthday value in by_monthday field. "
                        "Valid values: from 1 to 31 and from -31 to -1"
                    )
        return by_monthday

    def validate_interval(self, interval):
        if interval is not None:
            if not isinstance(interval, int) or interval <= 0:
                raise BadRequest(detail="Invalid value for interval")
        return interval

    def validate_rolling_users(self, rolling_users):
        result = []
        for users in rolling_users:
            users_dict = dict()
            for user in users:
                users_dict[user.pk] = user.public_primary_key
            result.append(users_dict)
        return result

    def _validate_frequency_and_week_start(self, event_type, frequency, interval, week_start):
        if event_type not in (CustomOnCallShift.TYPE_SINGLE_EVENT, CustomOnCallShift.TYPE_OVERRIDE):
            if frequency is None:
                raise BadRequest(detail="Field 'frequency' is required for this on-call shift type")
            elif frequency == CustomOnCallShift.FREQUENCY_WEEKLY and week_start is None:
                raise BadRequest(detail="Field 'week_start' is required for frequency type 'weekly'")
            # frequency is not None
            if interval is None:
                raise BadRequest(detail="Field 'interval' must be a positive integer")

    def _validate_frequency_daily(self, event_type, frequency, interval, by_day, by_monthday):
        if event_type == CustomOnCallShift.TYPE_ROLLING_USERS_EVENT:
            if frequency == CustomOnCallShift.FREQUENCY_DAILY:
                if by_monthday:
                    raise BadRequest(
                        detail="Day limits are temporarily disabled for on-call shifts with type 'rolling_users' "
                        "and frequency 'daily'"
                    )
                if by_day and interval > len(by_day):
                    raise BadRequest(detail="Interval must be less than or equal to the number of selected days")

    def _validate_start_rotation_from_user_index(self, type, index):
        if type == CustomOnCallShift.TYPE_ROLLING_USERS_EVENT and index is None:
            raise BadRequest(detail="Field 'start_rotation_from_user_index' is required for this on-call shift type")

    def _validate_date_format(self, value):
        try:
            time.strptime(value, "%Y-%m-%dT%H:%M:%S")
        except (TypeError, ValueError):
            raise BadRequest(detail="Invalid datetime format, should be \"yyyy-mm-dd'T'hh:mm:ss\"")

    def _validate_start(self, start):
        self._validate_date_format(start)

    def _validate_until(self, until):
        self._validate_date_format(until)

    def _validate_rotation_start(self, rotation_start):
        self._validate_date_format(rotation_start)

    def to_internal_value(self, data):
        if data.get("users", []) is None:  # terraform case
            data["users"] = []
        if data.get("rolling_users", []) is None:  # terraform case
            data["rolling_users"] = []
        if data.get("source") not in (CustomOnCallShift.SOURCE_TERRAFORM, CustomOnCallShift.SOURCE_WEB):
            data["source"] = CustomOnCallShift.SOURCE_API
        if data.get("start") is not None:
            self._validate_start(data["start"])
        if data.get("rotation_start") is not None:
            self._validate_rotation_start(data["rotation_start"])
        if data.get("until") is not None:
            self._validate_until(data["until"])
        result = super().to_internal_value(data)
        return result

    def to_representation(self, instance):
        result = super().to_representation(instance)
        result["duration"] = int(instance.duration.total_seconds())
        result["start"] = instance.start.strftime("%Y-%m-%dT%H:%M:%S")
        result["rotation_start"] = instance.rotation_start.strftime("%Y-%m-%dT%H:%M:%S")
        if instance.until is not None:
            result["until"] = instance.until.strftime("%Y-%m-%dT%H:%M:%S")
        result = self._get_fields_to_represent(instance, result)
        return result

    def _get_fields_to_represent(self, instance, result):
        event_type = instance.type
        fields_to_remove_map = {
            CustomOnCallShift.TYPE_SINGLE_EVENT: [
                "frequency",
                "interval",
                "until",
                "by_day",
                "by_month",
                "by_monthday",
                "week_start",
                "rolling_users",
                "start_rotation_from_user_index",
            ],
            CustomOnCallShift.TYPE_RECURRENT_EVENT: ["rolling_users", "start_rotation_from_user_index"],
            CustomOnCallShift.TYPE_ROLLING_USERS_EVENT: ["users"],
            CustomOnCallShift.TYPE_OVERRIDE: [
                "level",
                "frequency",
                "interval",
                "until",
                "by_day",
                "by_month",
                "by_monthday",
                "week_start",
                "rolling_users",
                "start_rotation_from_user_index",
            ],
        }
        for field in fields_to_remove_map[event_type]:
            result.pop(field, None)

        # represent field week_start only for events with frequency "weekly"
        if instance.frequency != CustomOnCallShift.FREQUENCY_WEEKLY:
            result.pop("week_start", None)

        return result

    def _correct_validated_data(self, event_type, validated_data):
        fields_to_update_map = {
            CustomOnCallShift.TYPE_SINGLE_EVENT: [
                "frequency",
                "interval",
                "by_day",
                "by_month",
                "by_monthday",
                "rolling_users",
                "start_rotation_from_user_index",
            ],
            CustomOnCallShift.TYPE_RECURRENT_EVENT: ["rolling_users", "start_rotation_from_user_index"],
            CustomOnCallShift.TYPE_ROLLING_USERS_EVENT: ["users"],
            CustomOnCallShift.TYPE_OVERRIDE: [
                "priority_level",
                "frequency",
                "interval",
                "by_day",
                "by_month",
                "by_monthday",
                "rolling_users",
                "start_rotation_from_user_index",
                "until",
            ],
        }
        for field in fields_to_update_map[event_type]:
            value = None
            if field == "users":
                value = []
            elif field == "priority_level":
                value = 0
            validated_data[field] = value

        validated_data_list_fields = ["by_day", "by_month", "by_monthday", "rolling_users"]

        for field in validated_data_list_fields:
            if isinstance(validated_data.get(field), list) and len(validated_data[field]) == 0:
                validated_data[field] = None
        if validated_data.get("start") is not None:
            validated_data["start"] = validated_data["start"].replace(tzinfo=None)
        if validated_data.get("frequency") and validated_data.get("interval") is None:
            # if there is frequency but no interval is given, default to 1
            validated_data["interval"] = 1

        # Populate "rolling_users" field using "users" field for web overrides
        # This emulates the behavior of the web UI, which creates overrides populating the rolling_users field
        # Also set the "priority_level" to 99 and "rotation_start" to "start" so it's consistent with the web UI
        # See apps.api.serializers.on_call_shifts.OnCallShiftSerializer for more info
        if (
            event_type == CustomOnCallShift.TYPE_OVERRIDE
            and validated_data.get("source") == CustomOnCallShift.SOURCE_WEB
        ):
            validated_data["rolling_users"] = [{str(u.pk): u.public_primary_key} for u in validated_data["users"]]
            validated_data["priority_level"] = 99
            validated_data["rotation_start"] = validated_data["start"]

        return validated_data


class CustomOnCallShiftUpdateSerializer(CustomOnCallShiftSerializer):
    type = CustomOnCallShiftTypeField(required=False)
    duration = serializers.DurationField(required=False)
    name = serializers.CharField(required=False)
    start = serializers.DateTimeField(required=False)
    rotation_start = serializers.DateTimeField(required=False)

    def update(self, instance, validated_data):
        event_type = validated_data.get("type", instance.type)
        frequency = validated_data.get("frequency", instance.frequency)
        start_rotation_from_user_index = validated_data.get(
            "start_rotation_from_user_index", instance.start_rotation_from_user_index
        )
        week_start = validated_data.get("week_start")
        interval = validated_data.get("interval", instance.interval)
        if frequency != instance.frequency:
            self._validate_frequency_and_week_start(event_type, frequency, interval, week_start)

        by_day = validated_data.get("by_day", instance.by_day)
        by_monthday = validated_data.get("by_monthday", instance.by_monthday)
        self._validate_frequency_daily(event_type, frequency, interval, by_day, by_monthday)

        if start_rotation_from_user_index != instance.start_rotation_from_user_index:
            self._validate_start_rotation_from_user_index(event_type, start_rotation_from_user_index)
        validated_data = self._correct_validated_data(event_type, validated_data)
        result = super().update(instance, validated_data)
        for schedule in instance.schedules.all():
            instance.start_drop_ical_and_check_schedule_tasks(schedule)
        return result
