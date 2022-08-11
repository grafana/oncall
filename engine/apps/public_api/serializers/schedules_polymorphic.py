from rest_framework.fields import empty
from rest_polymorphic.serializers import PolymorphicSerializer

from apps.public_api.serializers.schedules_calendar import ScheduleCalendarSerializer, ScheduleCalendarUpdateSerializer
from apps.public_api.serializers.schedules_ical import ScheduleICalSerializer, ScheduleICalUpdateSerializer
from apps.public_api.serializers.schedules_web import ScheduleWebSerializer, ScheduleWebUpdateSerializer
from apps.schedules.models import OnCallScheduleCalendar, OnCallScheduleICal, OnCallScheduleWeb
from common.api_helpers.mixins import EagerLoadingMixin


class PolymorphicScheduleSerializer(EagerLoadingMixin, PolymorphicSerializer):
    SELECT_RELATED = ["organization"]

    resource_type_field_name = "type"

    model_serializer_mapping = {
        OnCallScheduleICal: ScheduleICalSerializer,
        OnCallScheduleCalendar: ScheduleCalendarSerializer,
        OnCallScheduleWeb: ScheduleWebSerializer,
    }

    SCHEDULE_CLASS_TO_TYPE = {OnCallScheduleCalendar: "calendar", OnCallScheduleICal: "ical", OnCallScheduleWeb: "web"}

    def to_resource_type(self, model_or_instance):
        return self.SCHEDULE_CLASS_TO_TYPE.get(model_or_instance._meta.model)


class PolymorphicScheduleUpdateSerializer(PolymorphicScheduleSerializer):
    model_serializer_mapping = {
        OnCallScheduleICal: ScheduleICalUpdateSerializer,
        OnCallScheduleCalendar: ScheduleCalendarUpdateSerializer,
        OnCallScheduleWeb: ScheduleWebUpdateSerializer,
    }

    def update(self, instance, validated_data):
        """Overridden method of PolymorphicSerializer, here we get serializer from instance instead of validated data"""
        serializer = self._get_serializer_from_model_or_instance(instance)
        return serializer.update(instance, validated_data)

    def to_internal_value(self, data):
        """Overridden method of PolymorphicSerializer, here we get serializer from instance instead of data"""
        serializer = self._get_serializer_from_model_or_instance(self.instance)
        ret = serializer.to_internal_value(data)
        return ret

    def run_validation(self, data=empty):
        """Overridden method of PolymorphicSerializer, here we get serializer from instance instead of data"""
        serializer = self._get_serializer_from_model_or_instance(self.instance)
        validated_data = serializer.run_validation(data)
        return validated_data
