from django.apps import apps
from rest_framework import serializers

from apps.alerts.models import AlertReceiveChannel, ChannelFilter, EscalationChain
from apps.base.messaging import get_messaging_backend_from_id
from apps.telegram.models import TelegramToOrganizationConnector
from common.api_helpers.custom_fields import OrganizationFilteredPrimaryKeyRelatedField
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import EagerLoadingMixin, OrderedModelSerializerMixin
from common.utils import is_regex_valid


class ChannelFilterSerializer(OrderedModelSerializerMixin, EagerLoadingMixin, serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    alert_receive_channel = OrganizationFilteredPrimaryKeyRelatedField(queryset=AlertReceiveChannel.objects)
    escalation_chain = OrganizationFilteredPrimaryKeyRelatedField(
        queryset=EscalationChain.objects,
        filter_field="organization",
        allow_null=True,
        required=False,
    )
    slack_channel = serializers.SerializerMethodField()
    telegram_channel = OrganizationFilteredPrimaryKeyRelatedField(
        queryset=TelegramToOrganizationConnector.objects, filter_field="organization", allow_null=True, required=False
    )
    order = serializers.IntegerField(required=False)

    SELECT_RELATED = ["escalation_chain", "alert_receive_channel"]

    class Meta:
        model = ChannelFilter
        fields = [
            "id",
            "order",
            "alert_receive_channel",
            "escalation_chain",
            "slack_channel",
            "created_at",
            "filtering_term",
            "telegram_channel",
            "is_default",
            "notify_in_slack",
            "notify_in_telegram",
            "notification_backends",
        ]
        read_only_fields = ["created_at", "is_default"]
        extra_kwargs = {"filtering_term": {"required": True, "allow_null": False}}

    def get_slack_channel(self, obj):
        if obj.slack_channel_id is None:
            return None
        # display_name and id appears via annotate in ChannelFilterView.get_queryset()
        return {
            "display_name": obj.slack_channel_name,
            "slack_id": obj.slack_channel_id,
            "id": obj.slack_channel_pk,
        }

    def validate(self, attrs):
        alert_receive_channel = attrs.get("alert_receive_channel") or self.instance.alert_receive_channel
        filtering_term = attrs.get("filtering_term")
        if filtering_term is None:
            return attrs
        try:
            obj = ChannelFilter.objects.get(alert_receive_channel=alert_receive_channel, filtering_term=filtering_term)
        except ChannelFilter.DoesNotExist:
            return attrs
        if self.instance and obj.id == self.instance.id:
            return attrs
        else:
            raise serializers.ValidationError(
                {"filtering_term": ["Channel filter with this filtering term already exists"]}
            )

    def validate_slack_channel(self, slack_channel_id):
        SlackChannel = apps.get_model("slack", "SlackChannel")

        if slack_channel_id is not None:
            slack_channel_id = slack_channel_id.upper()
            organization = self.context["request"].auth.organization
            try:
                organization.slack_team_identity.get_cached_channels().get(slack_id=slack_channel_id)
            except SlackChannel.DoesNotExist:
                raise serializers.ValidationError(["Slack channel does not exist"])
        return slack_channel_id

    def validate_filtering_term(self, filtering_term):
        if filtering_term is not None:
            if not is_regex_valid(filtering_term):
                raise serializers.ValidationError(["Filtering term is incorrect"])
        return filtering_term

    def validate_notification_backends(self, notification_backends):
        # NOTE: updates the whole field, handling dict updates per backend
        if notification_backends is not None:
            organization = self.context["request"].auth.organization
            if not isinstance(notification_backends, dict):
                raise serializers.ValidationError(["Invalid messaging backend data"])
            updated = self.instance.notification_backends or {}
            for backend_id in notification_backends:
                backend = get_messaging_backend_from_id(backend_id)
                if backend is None:
                    raise serializers.ValidationError(["Invalid messaging backend"])
                updated_data = backend.validate_channel_filter_data(
                    organization,
                    notification_backends[backend_id],
                )
                # update existing backend data
                updated[backend_id] = updated.get(backend_id, {}) | updated_data
            notification_backends = updated
        return notification_backends


class ChannelFilterCreateSerializer(ChannelFilterSerializer):
    alert_receive_channel = OrganizationFilteredPrimaryKeyRelatedField(queryset=AlertReceiveChannel.objects)
    slack_channel = serializers.CharField(allow_null=True, required=False, source="slack_channel_id")

    class Meta:
        model = ChannelFilter
        fields = [
            "id",
            "order",
            "alert_receive_channel",
            "escalation_chain",
            "slack_channel",
            "created_at",
            "filtering_term",
            "telegram_channel",
            "is_default",
            "notify_in_slack",
            "notify_in_telegram",
            "notification_backends",
        ]
        read_only_fields = ["created_at", "is_default"]
        extra_kwargs = {"filtering_term": {"required": True, "allow_null": False}}

    def to_representation(self, obj):
        """add correct slack channel data to result after instance creation/update"""
        result = super().to_representation(obj)
        if obj.slack_channel_id is None:
            result["slack_channel"] = None
        else:
            slack_team_identity = self.context["request"].auth.organization.slack_team_identity
            if slack_team_identity is not None:
                slack_channel = slack_team_identity.get_cached_channels(slack_id=obj.slack_channel_id).first()
                if slack_channel:
                    result["slack_channel"] = {
                        "display_name": slack_channel.name,
                        "slack_id": obj.slack_channel_id,
                        "id": slack_channel.public_primary_key,
                    }
        return result

    def create(self, validated_data):
        order = validated_data.pop("order", None)
        if order is not None:
            alert_receive_channel_id = validated_data.get("alert_receive_channel")
            self._validate_order(order, {"alert_receive_channel_id": alert_receive_channel_id, "is_default": False})
            instance = super().create(validated_data)
            self._change_position(order, instance)
        else:
            instance = super().create(validated_data)
        return instance


class ChannelFilterUpdateSerializer(ChannelFilterCreateSerializer):
    alert_receive_channel = OrganizationFilteredPrimaryKeyRelatedField(read_only=True)

    class Meta(ChannelFilterCreateSerializer.Meta):
        read_only_fields = [*ChannelFilterCreateSerializer.Meta.read_only_fields, "alert_receive_channel"]
        extra_kwargs = {"filtering_term": {"required": False}}

    def update(self, instance, validated_data):
        order = validated_data.get("order")
        filtering_term = validated_data.get("filtering_term")

        if instance.is_default and order is not None and instance.order != order:
            raise BadRequest(detail="The order of default channel filter cannot be changed")

        if instance.is_default and filtering_term is not None:
            raise BadRequest(detail="Filtering term of default channel filter cannot be changed")

        if order is not None:
            self._validate_order(
                order, {"alert_receive_channel_id": instance.alert_receive_channel_id, "is_default": False}
            )
            self._change_position(order, instance)
        return super().update(instance, validated_data)
