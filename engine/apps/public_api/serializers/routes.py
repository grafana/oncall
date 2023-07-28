from rest_framework import fields, serializers

from apps.alerts.models import AlertReceiveChannel, ChannelFilter, EscalationChain
from apps.api.serializers.alert_receive_channel import valid_jinja_template_for_serializer_method_field
from apps.base.messaging import get_messaging_backend_from_id, get_messaging_backends
from common.api_helpers.custom_fields import OrganizationFilteredPrimaryKeyRelatedField
from common.api_helpers.exceptions import BadRequest
from common.jinja_templater.apply_jinja_template import JinjaTemplateError
from common.ordered_model.serializer import OrderedModelSerializer
from common.utils import is_regex_valid


class BaseChannelFilterSerializer(OrderedModelSerializer):
    """Base Channel Filter serializer with validation methods"""

    def __init__(self, *args, **kwargs):
        """Update existing fields of the serializer with messaging backends fields"""

        super().__init__(*args, **kwargs)
        for backend_id, backend in get_messaging_backends():
            if backend is None:
                continue
            field = backend.slug
            self._declared_fields[field] = serializers.DictField(required=False)
            self.Meta.fields.append(field)

    def to_representation(self, instance):
        result = super().to_representation(instance)
        result["slack"] = {"channel_id": instance.slack_channel_id, "enabled": bool(instance.notify_in_slack)}
        result["telegram"] = {
            "id": instance.telegram_channel.public_primary_key if instance.telegram_channel else None,
            "enabled": bool(instance.notify_in_telegram),
        }
        # add representation for other messaging backends
        for backend_id, backend in get_messaging_backends():
            if backend is None:
                continue
            field = backend.slug
            channel_id = None
            notification_enabled = False
            if instance.notification_backends and instance.notification_backends.get(backend_id):
                channel_id = instance.notification_backends[backend_id].get("channel")
                notification_enabled = bool(instance.notification_backends[backend_id].get("enabled"))
            result[field] = {"id": channel_id, "enabled": notification_enabled}
        return result

    def _correct_validated_data(self, validated_data):
        organization = self.context["request"].auth.organization

        slack_field = validated_data.pop("slack", {})
        if slack_field:
            if "channel_id" in slack_field:
                validated_data["slack_channel_id"] = self._validate_slack_channel_id(slack_field.get("channel_id"))
            if "enabled" in slack_field:
                validated_data["notify_in_slack"] = bool(slack_field.get("enabled"))

        telegram_field = validated_data.pop("telegram", {})
        if telegram_field:
            if "id" in telegram_field:
                validated_data["telegram_channel"] = self._validate_telegram_channel(telegram_field.get("id"))
            if "enabled" in telegram_field:
                validated_data["notify_in_telegram"] = bool(telegram_field.get("enabled"))

        notification_backends = {}
        for backend_id, backend in get_messaging_backends():
            if backend is None:
                continue
            field = backend.slug
            backend_field = validated_data.pop(field, {})
            if backend_field:
                notification_backend = {}
                if "id" in backend_field:
                    notification_backend["channel"] = backend_field["id"]
                if "enabled" in backend_field:
                    notification_backend["enabled"] = backend_field["enabled"]
                backend.validate_channel_filter_data(organization, notification_backend)
                notification_backends[backend_id] = notification_backend
        if notification_backends:
            validated_data["notification_backends"] = notification_backends
        return validated_data

    def _validate_slack_channel_id(self, slack_channel_id):
        from apps.slack.models import SlackChannel

        if slack_channel_id is not None:
            slack_channel_id = slack_channel_id.upper()
            organization = self.context["request"].auth.organization
            slack_team_identity = organization.slack_team_identity
            try:
                slack_team_identity.get_cached_channels().get(slack_id=slack_channel_id)
            except SlackChannel.DoesNotExist:
                raise BadRequest(detail="Slack channel does not exist")
        return slack_channel_id

    def _validate_telegram_channel(self, telegram_channel_id):
        from apps.telegram.models import TelegramToOrganizationConnector

        if telegram_channel_id is not None:
            organization = self.context["request"].auth.organization
            try:
                telegram_channel = organization.telegram_channel.get(public_primary_key=telegram_channel_id)
            except TelegramToOrganizationConnector.DoesNotExist:
                raise BadRequest(detail="Telegram channel does not exist")
            return telegram_channel
        return

    def _update_notification_backends(self, notification_backends):
        if notification_backends is not None:
            current = self.instance.notification_backends or {}
            for backend_id in notification_backends:
                backend = get_messaging_backend_from_id(backend_id)
                if backend is None:
                    continue
                # update existing backend data
                notification_backends[backend_id] = current.get(backend_id, {}) | notification_backends[backend_id]
        return notification_backends


class RoutingTypeField(fields.CharField):
    def to_representation(self, value):
        return ChannelFilter.FILTERING_TERM_TYPE_CHOICES[value][1]

    def to_internal_value(self, data):
        for filtering_term_type_choices in ChannelFilter.FILTERING_TERM_TYPE_CHOICES:
            if filtering_term_type_choices[1] == data:
                return filtering_term_type_choices[0]
        raise BadRequest(detail="Invalid route type")


class ChannelFilterSerializer(BaseChannelFilterSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    slack = serializers.DictField(required=False)
    telegram = serializers.DictField(required=False)
    routing_type = RoutingTypeField(allow_null=False, required=False, source="filtering_term_type")
    routing_regex = serializers.CharField(allow_null=False, required=True, source="filtering_term")
    integration_id = OrganizationFilteredPrimaryKeyRelatedField(
        queryset=AlertReceiveChannel.objects, source="alert_receive_channel"
    )
    escalation_chain_id = OrganizationFilteredPrimaryKeyRelatedField(
        queryset=EscalationChain.objects,
        source="escalation_chain",
        allow_null=True,
    )

    is_the_last_route = serializers.BooleanField(read_only=True, source="is_default")

    class Meta:
        model = ChannelFilter
        fields = OrderedModelSerializer.Meta.fields + [
            "id",
            "integration_id",
            "escalation_chain_id",
            "routing_type",
            "routing_regex",
            "is_the_last_route",
            "slack",
            "telegram",
        ]
        read_only_fields = ["is_the_last_route"]

    def create(self, validated_data):
        validated_data = self._correct_validated_data(validated_data)
        return super().create(validated_data)

    def validate(self, data):
        filtering_term = data.get("routing_regex")
        filtering_term_type = data.get("routing_type")
        if filtering_term_type == ChannelFilter.FILTERING_TERM_TYPE_JINJA2:
            try:
                valid_jinja_template_for_serializer_method_field({"route_template": filtering_term})
            except JinjaTemplateError:
                raise serializers.ValidationError(["Jinja template is incorrect"])
        elif filtering_term_type == ChannelFilter.FILTERING_TERM_TYPE_REGEX or filtering_term_type is None:
            if filtering_term is not None:
                if not is_regex_valid(filtering_term):
                    raise serializers.ValidationError(["Regular expression is incorrect"])
        else:
            raise serializers.ValidationError(["Expression type is incorrect"])
        return data


class ChannelFilterUpdateSerializer(ChannelFilterSerializer):
    integration_id = OrganizationFilteredPrimaryKeyRelatedField(source="alert_receive_channel", read_only=True)
    routing_regex = serializers.CharField(allow_null=False, required=False, source="filtering_term")
    escalation_chain_id = OrganizationFilteredPrimaryKeyRelatedField(
        queryset=EscalationChain.objects,
        source="escalation_chain",
        required=False,
    )

    class Meta(ChannelFilterSerializer.Meta):
        read_only_fields = [*ChannelFilterSerializer.Meta.read_only_fields, "integration_id"]

    def update(self, instance, validated_data):
        validated_data = self._correct_validated_data(validated_data)
        if validated_data.get("notification_backends"):
            validated_data["notification_backends"] = self._update_notification_backends(
                validated_data["notification_backends"]
            )

        return super().update(instance, validated_data)


class DefaultChannelFilterSerializer(BaseChannelFilterSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    slack = serializers.DictField(required=False)
    telegram = serializers.DictField(required=False)
    escalation_chain_id = OrganizationFilteredPrimaryKeyRelatedField(
        queryset=EscalationChain.objects,
        source="escalation_chain",
        allow_null=True,
        required=False,
    )

    class Meta:
        model = ChannelFilter
        fields = [
            "id",
            "slack",
            "telegram",
            "escalation_chain_id",
        ]

    def update(self, instance, validated_data):
        validated_data = self._correct_validated_data(validated_data)
        if validated_data.get("notification_backends"):
            validated_data["notification_backends"] = self._update_notification_backends(
                validated_data["notification_backends"]
            )
        return super().update(instance, validated_data)
