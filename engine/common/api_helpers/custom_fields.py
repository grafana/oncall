import time

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import fields, serializers
from rest_framework.exceptions import ValidationError
from rest_framework.relations import RelatedField

from apps.alerts.models import ChannelFilter
from apps.user_management.models import User
from common.api_helpers.exceptions import BadRequest


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


class WritableSerializerMethodField(serializers.SerializerMethodField):
    """
    Please, NEVER use this field.
    It was a mistake to create this one due to necessity to dig deep in drf to fix bugs there.
    This field is a workaround to allow to write into SerializerMethodField.
    """

    def __init__(self, method_name=None, **kwargs):
        self.method_name = method_name
        self.setter_method_name = kwargs.pop("setter_method_name", None)
        self.deserializer_field = kwargs.pop("deserializer_field")

        kwargs["source"] = "*"
        super(serializers.SerializerMethodField, self).__init__(**kwargs)

    def bind(self, field_name, parent):
        retval = super().bind(field_name, parent)
        if not self.setter_method_name:
            self.setter_method_name = f"set_{field_name}"

        return retval

    def to_internal_value(self, data):
        value = self.deserializer_field.to_internal_value(data)
        method = getattr(self.parent, self.setter_method_name)
        method(value)
        return {self.method_name: value}


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
