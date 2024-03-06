import datetime
import typing

from django.utils import timezone
from rest_framework import serializers

from apps.schedules.models import OnCallSchedule, ShiftSwapRequest
from common.api_helpers.custom_fields import OrganizationFilteredPrimaryKeyRelatedField, TimeZoneAwareDatetimeField
from common.api_helpers.mixins import EagerLoadingMixin

if typing.TYPE_CHECKING:
    from apps.user_management.models import User


class BaseShiftSwapRequestListSerializer(EagerLoadingMixin, serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    schedule = OrganizationFilteredPrimaryKeyRelatedField(queryset=OnCallSchedule.objects)

    created_at = TimeZoneAwareDatetimeField(read_only=True)
    updated_at = TimeZoneAwareDatetimeField(read_only=True)

    swap_start = TimeZoneAwareDatetimeField()
    swap_end = TimeZoneAwareDatetimeField()

    beneficiary = serializers.CharField(read_only=True, source="beneficiary.public_primary_key")
    benefactor = serializers.SerializerMethodField(read_only=True)

    SELECT_RELATED = [
        "schedule",
        "beneficiary",
        "benefactor",
    ]

    class Meta:
        model = ShiftSwapRequest
        fields = [
            "id",
            "created_at",
            "updated_at",
            "status",
            "schedule",
            "swap_start",
            "swap_end",
            "description",
            "beneficiary",
            "benefactor",
        ]
        read_only_fields = [
            "status",
        ]


class ShiftSwapRequestListSerializer(BaseShiftSwapRequestListSerializer):
    def get_benefactor(self, obj: ShiftSwapRequest) -> str | None:
        return obj.benefactor.public_primary_key if obj.benefactor else None


class ShiftSwapRequestSerializer(ShiftSwapRequestListSerializer):
    class Meta(ShiftSwapRequestListSerializer.Meta):
        fields = ShiftSwapRequestListSerializer.Meta.fields + [
            "shifts",
        ]
        read_only_fields = ShiftSwapRequestListSerializer.Meta.read_only_fields + [
            "shifts",
        ]

    @staticmethod
    def validate_start_and_end_times(swap_start: datetime.datetime, swap_end: datetime.datetime) -> None:
        if timezone.now() > swap_start:
            raise serializers.ValidationError("swap_start must be a datetime in the future")
        if swap_start > swap_end:
            raise serializers.ValidationError("swap_end must occur after swap_start")

    def validate(self, data):
        swap_start = data.get("swap_start", None)
        swap_end = data.get("swap_end", None)

        if self.partial:  # self.partial is true when it's a "partial update" aka PATCH
            # if any time related field is specified then we will enforce that they must all be specified
            time_fields = [swap_start, swap_end]
            any_time_fields_specified = any(time_fields)
            all_time_fields_specified = all(time_fields)

            if any_time_fields_specified and not all_time_fields_specified:
                raise serializers.ValidationError(
                    "when doing a partial update on time related fields, both start and end times must be specified"
                )
            elif all_time_fields_specified:
                self.validate_start_and_end_times(swap_start, swap_end)
        else:
            self.validate_start_and_end_times(swap_start, swap_end)

        # TODO: we should validate that the beneficiary actually has shifts for the specified schedule
        # between swap_start and swap_end

        return data


class ShiftSwapRequestExpandedUsersListSerializer(BaseShiftSwapRequestListSerializer):
    beneficiary = serializers.SerializerMethodField(read_only=True)
    benefactor = serializers.SerializerMethodField(read_only=True)

    def _serialize_user(self, user: "User") -> dict | None:
        user_data = None
        if user:
            user_data = {
                "display_name": user.username,
                "email": user.email,
                "pk": user.public_primary_key,
                "avatar_full": user.avatar_full_url,
            }
        return user_data

    def get_benefactor(self, obj: ShiftSwapRequest) -> dict | None:
        return self._serialize_user(obj.benefactor)

    def get_beneficiary(self, obj: ShiftSwapRequest) -> dict | None:
        return self._serialize_user(obj.beneficiary)


class ShiftSwapRequestExpandedUsersSerializer(
    ShiftSwapRequestExpandedUsersListSerializer,
    ShiftSwapRequestSerializer,
):
    pass
