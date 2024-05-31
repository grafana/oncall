from datetime import timedelta

from rest_framework import serializers

from apps.base.models import UserNotificationPolicy
from apps.base.models.user_notification_policy import NotificationChannelAPIOptions
from apps.user_management.models import User
from common.api_helpers.custom_fields import DurationSecondsField, OrganizationFilteredPrimaryKeyRelatedField
from common.api_helpers.exceptions import Forbidden
from common.api_helpers.mixins import EagerLoadingMixin


# This serializer should not be user directly
class UserNotificationPolicyBaseSerializer(EagerLoadingMixin, serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    notify_by = serializers.ChoiceField(
        read_only=False,
        required=False,
        default=UserNotificationPolicy.NotificationChannel.SLACK,
        choices=NotificationChannelAPIOptions.AVAILABLE_FOR_USE,
    )
    step = serializers.ChoiceField(
        read_only=False,
        required=False,
        default=UserNotificationPolicy.Step.NOTIFY,
        choices=UserNotificationPolicy.Step.choices,
    )
    wait_delay = DurationSecondsField(
        required=False,
        allow_null=True,
        min_value=timedelta(minutes=1),
        max_value=timedelta(hours=24),
    )

    SELECT_RELATED = [
        "user",
    ]

    class Meta:
        model = UserNotificationPolicy
        fields = ["id", "step", "notify_by", "wait_delay", "important", "user"]

        # Field "order" is not consumed by the plugin frontend, but is used by the mobile app
        # TODO: remove this field when the mobile app is updated
        fields += ["order"]
        read_only_fields = ["order"]

    def to_internal_value(self, data):
        data = self._notify_by_to_internal_value(data)
        return super().to_internal_value(data)

    def to_representation(self, instance):
        result = super().to_representation(instance)
        result = self._notify_by_to_representation(instance, result)
        return result

    #  _notify_by_to_internal_value and _notify_by_to_representation are exists because of in EscalationPolicy model
    #  notify_by field has default value NotificationChannel.SLACK and not nullable
    #  We don't want any notify_by value in response if step != Step.NOTIFY
    def _notify_by_to_internal_value(self, data):
        if not data.get("notify_by", None):
            data["notify_by"] = UserNotificationPolicy.NotificationChannel.SLACK
        return data

    def _notify_by_to_representation(self, instance, result):
        if instance.step != UserNotificationPolicy.Step.NOTIFY:
            result["notify_by"] = None
        return result


class UserNotificationPolicySerializer(UserNotificationPolicyBaseSerializer):
    user = OrganizationFilteredPrimaryKeyRelatedField(
        queryset=User.objects,
        required=False,
        allow_null=True,
        many=False,
        display_func=lambda instance: instance.username,
    )
    notify_by = serializers.ChoiceField(
        choices=NotificationChannelAPIOptions.AVAILABLE_FOR_USE,
        default=NotificationChannelAPIOptions.DEFAULT_NOTIFICATION_CHANNEL,
    )

    def create(self, validated_data):
        user = validated_data.get("user") or self.context["request"].user
        organization = self.context["request"].auth.organization

        self_or_admin = user.self_or_admin(user_to_check=self.context["request"].user, organization=organization)
        if not self_or_admin:
            raise Forbidden()

        instance = UserNotificationPolicy.objects.create(**validated_data)
        return instance


class UserNotificationPolicyUpdateSerializer(UserNotificationPolicyBaseSerializer):
    user = OrganizationFilteredPrimaryKeyRelatedField(
        many=False,
        read_only=True,
        display_func=lambda instance: instance.username,
    )

    class Meta(UserNotificationPolicyBaseSerializer.Meta):
        read_only_fields = UserNotificationPolicyBaseSerializer.Meta.read_only_fields + ["user", "important"]

    def update(self, instance, validated_data):
        self_or_admin = instance.user.self_or_admin(
            user_to_check=self.context["request"].user, organization=self.context["request"].user.organization
        )
        if not self_or_admin:
            raise Forbidden()
        if validated_data.get("step") == UserNotificationPolicy.Step.WAIT and not validated_data.get("wait_delay"):
            validated_data["wait_delay"] = UserNotificationPolicy.FIVE_MINUTES
        return super().update(instance, validated_data)
