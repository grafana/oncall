from rest_polymorphic.serializers import PolymorphicSerializer

from apps.api.serializers.schedule_calendar import ScheduleCalendarCreateSerializer, ScheduleCalendarSerializer
from apps.api.serializers.schedule_ical import (
    ScheduleICalCreateSerializer,
    ScheduleICalSerializer,
    ScheduleICalUpdateSerializer,
)
from apps.api.serializers.schedule_web import ScheduleWebCreateSerializer, ScheduleWebSerializer
from apps.schedules.models import OnCallScheduleCalendar, OnCallScheduleICal, OnCallScheduleWeb
from common.api_helpers.mixins import EagerLoadingMixin


class PolymorphicScheduleSerializer(EagerLoadingMixin, PolymorphicSerializer):
    SELECT_RELATED = ["organization", "user_group"]

    resource_type_field_name = "type"

    model_serializer_mapping = {
        OnCallScheduleICal: ScheduleICalSerializer,
        OnCallScheduleCalendar: ScheduleCalendarSerializer,
        OnCallScheduleWeb: ScheduleWebSerializer,
    }

    SCHEDULE_CLASS_TO_TYPE = {OnCallScheduleCalendar: 0, OnCallScheduleICal: 1, OnCallScheduleWeb: 2}

    def to_resource_type(self, model_or_instance):
        return self.SCHEDULE_CLASS_TO_TYPE.get(model_or_instance._meta.model)


class PolymorphicScheduleCreateSerializer(PolymorphicScheduleSerializer):
    model_serializer_mapping = {
        OnCallScheduleICal: ScheduleICalCreateSerializer,
        OnCallScheduleCalendar: ScheduleCalendarCreateSerializer,
        OnCallScheduleWeb: ScheduleWebCreateSerializer,
    }


class PolymorphicScheduleUpdateSerializer(PolymorphicScheduleSerializer):
    model_serializer_mapping = {
        OnCallScheduleICal: ScheduleICalUpdateSerializer,
        # There is no difference between create and Update serializers for ScheduleCalendar
        OnCallScheduleCalendar: ScheduleCalendarCreateSerializer,
        OnCallScheduleWeb: ScheduleWebCreateSerializer,
    }
