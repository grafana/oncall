from django.apps import apps
from rest_framework import serializers

from apps.alerts.models import AlertReceiveChannel, ChannelFilter, EscalationChain
from apps.api.serializers.alert_receive_channel import valid_jinja_template_for_serializer_method_field
from apps.base.messaging import get_messaging_backend_from_id
from apps.telegram.models import TelegramToOrganizationConnector
from common.api_helpers.custom_fields import OrganizationFilteredPrimaryKeyRelatedField
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import EagerLoadingMixin, OrderedModelSerializerMixin
from common.jinja_templater.apply_jinja_template import JinjaTemplateError
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
    filtering_term_as_jinja2 = serializers.SerializerMethodField()

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
            "filtering_term_type",
            "telegram_channel",
            "is_default",
            "notify_in_slack",
            "notify_in_telegram",
            "notification_backends",
            "filtering_term_as_jinja2",
        ]
        read_only_fields = ["created_at", "is_default"]
        extra_kwargs = {"filtering_term": {"required": True, "allow_null": False}}

    def validate(self, data):
        filtering_term = data.get("filtering_term")
        filtering_term_type = data.get("filtering_term_type")
        if filtering_term_type == ChannelFilter.FILTERING_TERM_TYPE_JINJA2:
            try:
                valid_jinja_template_for_serializer_method_field({"route_template": filtering_term})
            except JinjaTemplateError:
                raise serializers.ValidationError([f"Jinja template is incorrect"])
        elif filtering_term_type == ChannelFilter.FILTERING_TERM_TYPE_REGEX or filtering_term_type is None:
            if filtering_term is not None:
                if not is_regex_valid(filtering_term):
                    raise serializers.ValidationError(["Regular expression is incorrect"])
        else:
            raise serializers.ValidationError([f"Expression type is incorrect"])
        return data

    def get_slack_channel(self, obj):
        if obj.slack_channel_id is None:
            return None
        # display_name and id appears via annotate in ChannelFilterView.get_queryset()
        return {
            "display_name": obj.slack_channel_name,
            "slack_id": obj.slack_channel_id,
            "id": obj.slack_channel_pk,
        }

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

    def get_filtering_term_as_jinja2(self, obj):
        """
        Returns the regex filtering term as a jinja2, for the preview before migration from regex to jinja2"""
        if obj.filtering_term_type == ChannelFilter.FILTERING_TERM_TYPE_JINJA2:
            return obj.filtering_term
        elif obj.filtering_term_type == ChannelFilter.FILTERING_TERM_TYPE_REGEX:
            # Four curly braces will result in two curly braces in the final string
            # rf"..." is a raw f string, to keep original filtering_term
            return rf'{{{{ payload | json_dumps | regex_search("{obj.filtering_term}") }}}}'


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
            "filtering_term_type",
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
