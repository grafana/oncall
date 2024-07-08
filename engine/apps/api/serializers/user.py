import math
import time
import typing

from django.conf import settings
from rest_framework import serializers

from apps.api.serializers.telegram import TelegramToUserConnectorSerializer
from apps.base.messaging import get_messaging_backends
from apps.base.models import UserNotificationPolicy
from apps.base.utils import live_settings
from apps.oss_installation.constants import CloudSyncStatus
from apps.oss_installation.utils import cloud_user_identity_status
from apps.schedules.ical_utils import SchedulesOnCallUsers
from apps.user_management.models import User
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField, TimeZoneField
from common.api_helpers.mixins import EagerLoadingMixin
from common.api_helpers.utils import check_phone_number_is_valid

from .custom_serializers import DynamicFieldsModelSerializer
from .organization import FastOrganizationSerializer
from .slack_user_identity import SlackUserIdentitySerializer
from .team import FastTeamSerializer


class UserSerializerContext(typing.TypedDict):
    schedules_with_oncall_users: SchedulesOnCallUsers


class UserPermissionSerializer(serializers.Serializer):
    action = serializers.CharField(read_only=True)


class GoogleCalendarSettingsSerializer(serializers.Serializer):
    # # TODO: figure out how to get OrganizationFilteredPrimaryKeyRelatedField to work with many=True
    # oncall_schedules_to_consider_for_shift_swaps =
    # oncall_schedules_to_consider_for_shift_swaps = serializers.ListField(
    #     child=OrganizationFilteredPrimaryKeyRelatedField(
    #         queryset=OnCallSchedule.objects,
    #         required=False,
    #         allow_null=True,
    #     ),
    #     required=False,
    #     allow_null=True,
    # )
    oncall_schedules_to_consider_for_shift_swaps = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_null=True,
    )


class NotificationChainVerbal(typing.TypedDict):
    default: str
    important: str


class WorkingHoursPeriodSerializer(serializers.Serializer):
    start = serializers.CharField()
    end = serializers.CharField()


class WorkingHoursSerializer(serializers.Serializer):
    monday = serializers.ListField(child=WorkingHoursPeriodSerializer())
    tuesday = serializers.ListField(child=WorkingHoursPeriodSerializer())
    wednesday = serializers.ListField(child=WorkingHoursPeriodSerializer())
    thursday = serializers.ListField(child=WorkingHoursPeriodSerializer())
    friday = serializers.ListField(child=WorkingHoursPeriodSerializer())
    saturday = serializers.ListField(child=WorkingHoursPeriodSerializer())
    sunday = serializers.ListField(child=WorkingHoursPeriodSerializer())


class ListUserSerializer(DynamicFieldsModelSerializer, EagerLoadingMixin):
    pk = serializers.CharField(read_only=True, source="public_primary_key")
    slack_user_identity = SlackUserIdentitySerializer(read_only=True)

    telegram_configuration = TelegramToUserConnectorSerializer(source="telegram_connection", read_only=True)

    messaging_backends = serializers.SerializerMethodField()

    organization = FastOrganizationSerializer(read_only=True)
    current_team = TeamPrimaryKeyRelatedField(allow_null=True, required=False)

    timezone = TimeZoneField(allow_null=True, required=False)
    avatar = serializers.URLField(source="avatar_url", read_only=True)
    avatar_full = serializers.URLField(source="avatar_full_url", read_only=True)
    notification_chain_verbal = serializers.SerializerMethodField()
    cloud_connection_status = serializers.SerializerMethodField()
    working_hours = WorkingHoursSerializer(required=False)

    SELECT_RELATED = [
        "telegram_verification_code",
        "telegram_connection",
        "organization",
        "slack_user_identity",
        "mobileappauthtoken",
        "google_oauth2_user",
    ]

    class Meta:
        model = User
        fields = [
            "pk",
            "organization",
            "current_team",
            "email",
            "username",
            "name",
            "role",
            "avatar",
            "avatar_full",
            "timezone",
            "working_hours",
            "unverified_phone_number",
            "verified_phone_number",
            "slack_user_identity",
            "telegram_configuration",
            "messaging_backends",
            "notification_chain_verbal",
            "cloud_connection_status",
            "hide_phone_number",
            "has_google_oauth2_connected",
        ]
        read_only_fields = [
            "email",
            "username",
            "name",
            "role",
            "verified_phone_number",
            "has_google_oauth2_connected",
        ]

    def validate_working_hours(self, working_hours):
        for day in working_hours:
            for period in working_hours[day]:
                try:
                    start = time.strptime(period["start"], "%H:%M:%S")
                    end = time.strptime(period["end"], "%H:%M:%S")
                except ValueError:
                    raise serializers.ValidationError("'start' and 'end' fields must be in '%H:%M:%S' format")

                if start >= end:
                    raise serializers.ValidationError("'start' must be less than 'end'")
        return working_hours

    def validate_unverified_phone_number(self, value):
        if value:
            if check_phone_number_is_valid(value):
                return value
            else:
                raise serializers.ValidationError(
                    "Phone number must be entered in the format: '+999999999'. From 8 to 15 digits allowed."
                )
        else:
            return None

    def get_messaging_backends(self, obj: User) -> dict[str, dict]:
        serialized_data = {}
        supported_backends = get_messaging_backends()
        for backend_id, backend in supported_backends:
            serialized_data[backend_id] = backend.serialize_user(obj)
        return serialized_data

    def get_notification_chain_verbal(self, obj: User) -> NotificationChainVerbal:
        default, important = UserNotificationPolicy.get_short_verbals_for_user(user=obj)
        return {"default": " - ".join(default), "important": " - ".join(important)}

    def get_cloud_connection_status(self, obj: User) -> CloudSyncStatus | None:
        is_open_source_with_cloud_notifications = self.context.get("is_open_source_with_cloud_notifications", None)
        is_open_source_with_cloud_notifications = (
            is_open_source_with_cloud_notifications
            if is_open_source_with_cloud_notifications is not None
            else settings.IS_OPEN_SOURCE and live_settings.GRAFANA_CLOUD_NOTIFICATIONS_ENABLED
        )
        if is_open_source_with_cloud_notifications:
            connector = self.context.get("connector", None)
            identities = self.context.get("cloud_identities", {})
            identity = identities.get(obj.email, None)
            status, _ = cloud_user_identity_status(connector, identity)
            return status
        return None

    def to_representation(self, instance):
        result = super().to_representation(instance)
        if instance.id != self.context["request"].user.id:
            if instance.hide_phone_number:
                if result["verified_phone_number"]:
                    result["verified_phone_number"] = self._hide_phone_number(result["verified_phone_number"])
                if result["unverified_phone_number"]:
                    result["unverified_phone_number"] = self._hide_phone_number(result["unverified_phone_number"])
        return result

    @staticmethod
    def _hide_phone_number(number: str):
        HIDE_SYMBOL = "*"
        SHOW_LAST_SYMBOLS = 4
        if len(number) <= 4:
            SHOW_LAST_SYMBOLS = math.ceil(len(number) / 2)
        return f"{HIDE_SYMBOL * (len(number) - SHOW_LAST_SYMBOLS)}{number[-SHOW_LAST_SYMBOLS:]}"


class UserSerializer(ListUserSerializer):
    context: UserSerializerContext

    is_currently_oncall = serializers.SerializerMethodField()
    google_calendar_settings = GoogleCalendarSettingsSerializer(required=False)

    class Meta(ListUserSerializer.Meta):
        fields = ListUserSerializer.Meta.fields + [
            "is_currently_oncall",
            "google_calendar_settings",
        ]
        read_only_fields = ListUserSerializer.Meta.read_only_fields + [
            "is_currently_oncall",
        ]

    def get_is_currently_oncall(self, obj: User) -> bool:
        # Serializer context is set here: apps.api.views.user.UserView.get_serializer_context.
        return any(obj in users for users in self.context.get("schedules_with_oncall_users", {}).values())


class CurrentUserSerializer(UserSerializer):
    rbac_permissions = UserPermissionSerializer(read_only=True, many=True, source="permissions")

    class Meta:
        model = User
        fields = UserSerializer.Meta.fields + [
            "rbac_permissions",
        ]
        read_only_fields = UserSerializer.Meta.read_only_fields


class UserHiddenFieldsSerializer(ListUserSerializer):
    fields_available_for_all_users = [
        "pk",
        "organization",
        "current_team",
        "username",
        "avatar",
        "timezone",
        "working_hours",
        "notification_chain_verbal",
    ]

    def to_representation(self, instance):
        ret = super(ListUserSerializer, self).to_representation(instance)
        if instance.id != self.context["request"].user.id:
            for field in ret:
                if field not in self.fields_available_for_all_users:
                    ret[field] = "******"
            ret["hidden_fields"] = True
        return ret


class ScheduleUserSerializer(ListUserSerializer):
    fields_to_keep = [
        "pk",
        "organization",
        "email",
        "username",
        "name",
        "avatar",
        "avatar_full",
        "timezone",
        "working_hours",
        "slack_user_identity",
        "telegram_configuration",
    ]

    def to_representation(self, instance):
        serialized = super(ListUserSerializer, self).to_representation(instance)
        ret = {field: value for field, value in serialized.items() if field in self.fields_to_keep}
        return ret


class FastUserSerializer(serializers.ModelSerializer):
    pk = serializers.CharField(source="public_primary_key")

    class Meta:
        model = User
        fields = [
            "pk",
            "username",
        ]
        read_only_fields = [
            "pk",
            "username",
        ]


class FilterUserSerializer(EagerLoadingMixin, serializers.ModelSerializer):
    value = serializers.CharField(source="public_primary_key")
    display_name = serializers.CharField(source="username")

    class Meta:
        model = User
        fields = ["value", "display_name"]
        read_only_fields = [
            "pk",
            "username",
        ]


class UserShortSerializer(serializers.ModelSerializer):
    username = serializers.CharField()
    pk = serializers.CharField(source="public_primary_key")
    avatar = serializers.CharField(source="avatar_url")
    avatar_full = serializers.CharField(source="avatar_full_url")

    class Meta:
        model = User
        fields = [
            "username",
            "pk",
            "avatar",
            "avatar_full",
        ]
        read_only_fields = [
            "username",
            "pk",
            "avatar",
            "avatar_full",
        ]


class UserIsCurrentlyOnCallSerializer(UserShortSerializer, EagerLoadingMixin):
    context: UserSerializerContext

    teams = FastTeamSerializer(read_only=True, many=True)
    is_currently_oncall = serializers.SerializerMethodField()

    SELECT_RELATED = ["organization"]
    PREFETCH_RELATED = ["teams"]

    class Meta(UserShortSerializer.Meta):
        fields = UserShortSerializer.Meta.fields + [
            "name",
            "timezone",
            "teams",
            "is_currently_oncall",
        ]

    def get_is_currently_oncall(self, obj: User) -> bool:
        # Serializer context is set here: apps.api.views.user.UserView.get_serializer_context.
        return any(obj in users for users in self.context.get("schedules_with_oncall_users", {}).values())


class PagedUserSerializer(serializers.Serializer):
    class Meta:
        fields = [
            "username",
            "pk",
            "avatar",
            "avatar_full",
            "important",
        ]
