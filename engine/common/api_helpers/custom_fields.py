import time

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import fields, serializers
from rest_framework.exceptions import ValidationError
from rest_framework.relations import RelatedField

from apps.alerts.models import ChannelFilter
from apps.user_management.models import User
from common.api_helpers.exceptions import BadRequest
from common.timezones import raise_exception_if_not_valid_timezone


class OrganizationFilteredPrimaryKeyRelatedField(RelatedField):
    """
    This field is used to filter entities by organization
    """

    def __init__(self, **kwargs):
        self.filter_field = kwargs.pop("filter_field", "organization")
        self.display_func = kwargs.pop("display_func", lambda instance: str(instance))
        super().__init__(**kwargs)

    def to_representation(self, value):
        return value.public_primary_key

    def to_internal_value(self, data):
        try:
            return self.get_queryset().get(public_primary_key=data)
        except ObjectDoesNotExist:
            raise ValidationError("Object does not exist")
        except (TypeError, ValueError):
            raise ValidationError("Invalid values")

    def get_queryset(self):
        request = self.context.get("request", None)
        queryset = self.queryset
        if not request or not queryset:
            return None
        filter_kwargs = {self.filter_field: request.auth.organization}
        return queryset.filter(**filter_kwargs).distinct()

    def display_value(self, instance):
        return self.display_func(instance)


class TeamPrimaryKeyRelatedField(RelatedField):
    """
    This field is used to get user teams
    """

    def __init__(self, **kwargs):
        self.display_func = kwargs.pop("display_func", lambda instance: str(instance))
        super().__init__(**kwargs)

    def to_representation(self, value):
        return value.public_primary_key

    def to_internal_value(self, data):
        try:
            return self.get_queryset().get(public_primary_key=data)
        except ObjectDoesNotExist:
            raise ValidationError("Object does not exist")
        except (TypeError, ValueError):
            raise ValidationError("Invalid values")

    def get_queryset(self):
        request = self.context.get("request", None)
        if not request:
            return None
        return request.user.available_teams.all()

    def display_value(self, instance):
        return self.display_func(instance)

    def validate_empty_values(self, data):
        if data == "null":
            data = None
        return super().validate_empty_values(data)


class UsersFilteredByOrganizationField(serializers.Field):
    """
    This field reduces queries count when accessing User many related field (ex: notify_to_users_queue).
    Check if you can use OrganizationFilteredPrimaryKeyRelatedField before using this one.
    """

    def __init__(self, **kwargs):
        self.queryset = kwargs.pop("queryset", None)
        super().__init__(**kwargs)

    def to_representation(self, value):
        return list(map(lambda v: v.public_primary_key, value.all()))

    def to_internal_value(self, data):
        queryset = self.queryset
        request = self.context.get("request", None)

        if not request or not queryset:
            return None

        return queryset.filter(organization=request.user.organization, public_primary_key__in=data).distinct()


class CustomTimeField(fields.TimeField):
    def to_representation(self, value):
        result = super().to_representation(value)
        if result[-1] != "Z":
            result += "Z"
        return result

    def to_internal_value(self, data):
        TIME_FORMAT_LEN = len("00:00:00Z")
        if len(data) == TIME_FORMAT_LEN:
            try:
                time.strptime(data, "%H:%M:%SZ")
            except ValueError:
                raise BadRequest(detail="Invalid time format, should be '00:00:00Z'")
        else:
            raise BadRequest(detail="Invalid time format, should be '00:00:00Z'")
        return data


class RouteIdField(fields.CharField):
    def to_internal_value(self, data):
        try:
            channel_filter = ChannelFilter.objects.get(public_primary_key=data)
        except ChannelFilter.DoesNotExist:
            raise BadRequest(detail="Route does not exist")
        return channel_filter

    def to_representation(self, value):
        if value is not None:
            return value.public_primary_key
        return value


class UserIdField(fields.CharField):
    def to_internal_value(self, data):
        request = self.context.get("request", None)

        user = User.objects.filter(organization=request.auth.organization, public_primary_key=data).first()
        if user is None:
            raise BadRequest(detail="User does not exist")
        return user

    def to_representation(self, value):
        if value is not None:
            return value.public_primary_key
        return value


class RollingUsersField(serializers.ListField):
    def to_representation(self, value):
        result = [list(d.values()) for d in value]
        return result


class TimeZoneField(serializers.CharField):
    def _validator(self, value: str):
        raise_exception_if_not_valid_timezone(value, serializers.ValidationError)

    def __init__(self, **kwargs):
        super().__init__(validators=[self._validator], **kwargs)


class TimeZoneAwareDatetimeField(serializers.DateTimeField):
    """
    This serializer field ensures that datetimes are always
    passed in ISO-8601 format (https://en.wikipedia.org/wiki/ISO_8601) with one caveat, timezone information MUST
    be passed in. ISO-8601 allows timezone information to be optional.

    All of the following would be considered valid datetimes by this field:
    2023-07-20T18:35:19+00:00
    2023-07-20T18:35:19Z

    These are not valid:
    2023-07-20 12:00:00
    20230720T120000Z

    This allows us to capture timezone information at insert/update time. Django converts/persists this information
    in UTC, and then when it is read back, you can be 100% sure that you are working with a UTC timezone aware datetime.

    Additionally, it standardizes how we format returned datetime strings.
    """

    UTC_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
    UTC_FORMAT_WITH_MICROSECONDS = "%Y-%m-%dT%H:%M:%S.%fZ"

    UTC_OFFSET_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
    UTC_OFFSET_FORMAT_WITH_MICROSECONDS = "%Y-%m-%dT%H:%M:%S.%f%z"
    "`%z` = UTC offset in the form +HHMM or -HHMM. (a colon separator can optionally be included)"

    def __init__(self, **kwargs):
        # we could use 'iso-8601' as a valid value to input_formats, however, see the note above about it
        # allowing timezone naive datetimes
        super().__init__(
            format=self.UTC_FORMAT_WITH_MICROSECONDS,
            input_formats=[
                self.UTC_FORMAT,
                self.UTC_FORMAT_WITH_MICROSECONDS,
                self.UTC_OFFSET_FORMAT,
                self.UTC_OFFSET_FORMAT_WITH_MICROSECONDS,
            ],
            **kwargs,
        )
