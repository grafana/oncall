import math
import time

from django.conf import settings
from rest_framework import serializers

from apps.api.serializers.telegram import TelegramToUserConnectorSerializer
from apps.base.messaging import get_messaging_backends
from apps.base.models import UserNotificationPolicy
from apps.base.utils import live_settings
from apps.oss_installation.utils import cloud_user_identity_status
from apps.user_management.models import User
from apps.user_management.models.user import default_working_hours
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField, TimeZoneField
from common.api_helpers.mixins import EagerLoadingMixin
from common.api_helpers.utils import check_phone_number_is_valid

from .custom_serializers import DynamicFieldsModelSerializer
from .organization import FastOrganizationSerializer
from .slack_user_identity import SlackUserIdentitySerializer


class UserPermissionSerializer(serializers.Serializer):
    action = serializers.CharField(read_only=True)


class UserSerializer(DynamicFieldsModelSerializer, EagerLoadingMixin):
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

    SELECT_RELATED = ["telegram_verification_code", "telegram_connection", "organization", "slack_user_identity"]

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
        ]
        read_only_fields = [
            "email",
            "username",
            "name",
            "role",
            "verified_phone_number",
        ]

    def validate_working_hours(self, working_hours):
        if not isinstance(working_hours, dict):
            raise serializers.ValidationError("must be dict")

        # check that all days are present
        if sorted(working_hours.keys()) != sorted(default_working_hours().keys()):
            raise serializers.ValidationError("missing some days")

        for day in working_hours:
            periods = working_hours[day]

            if not isinstance(periods, list):
                raise serializers.ValidationError("periods must be list")

            for period in periods:
                if not isinstance(period, dict):
                    raise serializers.ValidationError("period must be dict")

                if sorted(period.keys()) != sorted(["start", "end"]):
                    raise serializers.ValidationError("'start' and 'end' fields must be present")

                if not isinstance(period["start"], str) or not isinstance(period["end"], str):
                    raise serializers.ValidationError("'start' and 'end' fields must be str")

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

    def get_messaging_backends(self, obj):
        serialized_data = {}
        supported_backends = get_messaging_backends()
        for backend_id, backend in supported_backends:
            serialized_data[backend_id] = backend.serialize_user(obj)
        return serialized_data

    def get_notification_chain_verbal(self, obj):
        default, important = UserNotificationPolicy.get_short_verbals_for_user(user=obj)
        return {"default": " - ".join(default), "important": " - ".join(important)}

    def get_cloud_connection_status(self, obj):
        if settings.IS_OPEN_SOURCE and live_settings.GRAFANA_CLOUD_NOTIFICATIONS_ENABLED:
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


class CurrentUserSerializer(UserSerializer):
    rbac_permissions = UserPermissionSerializer(read_only=True, many=True, source="permissions")

    class Meta:
        model = User
        fields = UserSerializer.Meta.fields + [
            "rbac_permissions",
        ]
        read_only_fields = UserSerializer.Meta.read_only_fields


class UserHiddenFieldsSerializer(UserSerializer):
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
        ret = super(UserSerializer, self).to_representation(instance)
        if instance.id != self.context["request"].user.id:
            for field in ret:
                if field not in self.fields_available_for_all_users:
                    ret[field] = "******"
            ret["hidden_fields"] = True
        return ret


class ScheduleUserSerializer(UserSerializer):
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
        serialized = super(UserSerializer, self).to_representation(instance)
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
