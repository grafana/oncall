from django.conf import settings
from rest_framework import serializers

from apps.api.serializers.telegram import TelegramToUserConnectorSerializer
from apps.base.constants import ADMIN_PERMISSIONS, ALL_ROLES_PERMISSIONS, EDITOR_PERMISSIONS
from apps.base.messaging import get_messaging_backends
from apps.base.models import UserNotificationPolicy
from apps.base.utils import live_settings
from apps.twilioapp.utils import check_phone_number_is_valid
from apps.user_management.models import User
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField
from common.api_helpers.mixins import EagerLoadingMixin
from common.constants.role import Role

from .custom_serializers import DynamicFieldsModelSerializer
from .organization import FastOrganizationSerializer
from .slack_user_identity import SlackUserIdentitySerializer


class UserSerializer(DynamicFieldsModelSerializer, EagerLoadingMixin):
    pk = serializers.CharField(read_only=True, source="public_primary_key")
    slack_user_identity = SlackUserIdentitySerializer(read_only=True)

    telegram_configuration = TelegramToUserConnectorSerializer(source="telegram_connection", read_only=True)

    messaging_backends = serializers.SerializerMethodField()

    organization = FastOrganizationSerializer(read_only=True)
    current_team = TeamPrimaryKeyRelatedField(allow_null=True, required=False)

    avatar = serializers.URLField(source="avatar_url", read_only=True)

    permissions = serializers.SerializerMethodField()
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
            "role",
            "avatar",
            "unverified_phone_number",
            "verified_phone_number",
            "slack_user_identity",
            "telegram_configuration",
            "messaging_backends",
            "permissions",
            "notification_chain_verbal",
            "cloud_connection_status",
        ]
        read_only_fields = [
            "email",
            "username",
            "role",
            "verified_phone_number",
        ]

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

    def get_permissions(self, obj):
        if obj.role == Role.ADMIN:
            return ADMIN_PERMISSIONS
        elif obj.role == Role.EDITOR:
            return EDITOR_PERMISSIONS
        else:
            return ALL_ROLES_PERMISSIONS

    def get_notification_chain_verbal(self, obj):
        default, important = UserNotificationPolicy.get_short_verbals_for_user(user=obj)
        return {"default": " - ".join(default), "important": " - ".join(important)}

    def get_cloud_connection_status(self, obj):
        if settings.OSS_INSTALLATION:
            if live_settings.GRAFANA_CLOUD_NOTIFICATIONS_ENABLED:
                from apps.oss_installation import constants as oss_constants

                connector = self.context.get("connector", None)
                identities = self.context.get("cloud_identities", {})
                identity = identities.get(obj.email, None)
                if connector is None:
                    return oss_constants.CLOUD_NOT_SYNCED
                if identity is None:
                    return oss_constants.CLOUD_SYNCED_USER_NOT_FOUND
                else:
                    if identity.phone_number_verified:
                        return oss_constants.CLOUD_SYNCED_PHONE_VERIFIED
                    else:
                        return oss_constants.CLOUD_SYNCED_PHONE_NOT_VERIFIED
        return None


class UserHiddenFieldsSerializer(UserSerializer):
    available_for_all_roles_fields = [
        "pk",
        "organization",
        "current_team",
        "username",
        "avatar",
        "notification_chain_verbal",
        "permissions",
    ]

    def to_representation(self, instance):
        ret = super(UserSerializer, self).to_representation(instance)
        for field in ret:
            if field not in self.available_for_all_roles_fields:
                ret[field] = "******"
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
