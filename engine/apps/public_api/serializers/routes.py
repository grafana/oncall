from django.apps import apps
from rest_framework import serializers

from apps.alerts.models import AlertReceiveChannel, ChannelFilter, EscalationChain
from common.api_helpers.custom_fields import OrganizationFilteredPrimaryKeyRelatedField
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import OrderedModelSerializerMixin


class ChannelFilterSerializer(OrderedModelSerializerMixin, serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    slack = serializers.DictField(required=False)
    routing_regex = serializers.CharField(allow_null=False, required=True, source="filtering_term")
    position = serializers.IntegerField(required=False, source="order")
    integration_id = OrganizationFilteredPrimaryKeyRelatedField(
        queryset=AlertReceiveChannel.objects, source="alert_receive_channel"
    )
    escalation_chain_id = OrganizationFilteredPrimaryKeyRelatedField(
        queryset=EscalationChain.objects,
        source="escalation_chain",
    )

    is_the_last_route = serializers.BooleanField(read_only=True, source="is_default")
    manual_order = serializers.BooleanField(default=False, write_only=True)

    class Meta:
        model = ChannelFilter
        fields = [
            "id",
            "integration_id",
            "escalation_chain_id",
            "routing_regex",
            "position",
            "is_the_last_route",
            "slack",
            "manual_order",
        ]
        read_only_fields = ("is_the_last_route",)

    def to_representation(self, instance):
        result = super().to_representation(instance)
        result["slack"] = {"channel_id": instance.slack_channel_id}
        return result

    def create(self, validated_data):
        validated_data = self._correct_validated_data(validated_data)
        manual_order = validated_data.pop("manual_order")
        if not manual_order:
            order = validated_data.pop("order", None)
            alert_receive_channel_id = validated_data.get("alert_receive_channel")
            # validate 'order' value before creation
            self._validate_order(order, {"alert_receive_channel_id": alert_receive_channel_id, "is_default": False})
            instance = super().create(validated_data)
            self._change_position(order, instance)
        else:
            instance = super().create(validated_data)

        return instance

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
            raise BadRequest(detail="Route with this regex already exists")

    def validate_escalation_chain_id(self, escalation_chain):
        if self.instance is not None:
            alert_receive_channel = self.instance.alert_receive_channel
        else:
            alert_receive_channel = AlertReceiveChannel.objects.get(
                public_primary_key=self.initial_data["integration_id"]
            )

        if escalation_chain.team != alert_receive_channel.team:
            raise BadRequest(detail="Escalation chain must be assigned to the same team as the integration")

        return escalation_chain

    def _correct_validated_data(self, validated_data):
        slack_field = validated_data.pop("slack", {})
        if "channel_id" in slack_field:
            validated_data["slack_channel_id"] = self._validate_slack_channel_id(slack_field.get("channel_id"))
        return validated_data

    def _validate_slack_channel_id(self, slack_channel_id):
        SlackChannel = apps.get_model("slack", "SlackChannel")

        if slack_channel_id is not None:
            slack_channel_id = slack_channel_id.upper()
            organization = self.context["request"].auth.organization
            slack_team_identity = organization.slack_team_identity
            try:
                slack_team_identity.get_cached_channels().get(slack_id=slack_channel_id)
            except SlackChannel.DoesNotExist:
                raise BadRequest(detail="Slack channel does not exist")
        return slack_channel_id


class ChannelFilterUpdateSerializer(ChannelFilterSerializer):
    integration_id = OrganizationFilteredPrimaryKeyRelatedField(source="alert_receive_channel", read_only=True)
    routing_regex = serializers.CharField(allow_null=False, required=False, source="filtering_term")

    class Meta(ChannelFilterSerializer.Meta):
        read_only_fields = [*ChannelFilterSerializer.Meta.read_only_fields, "integration_id"]

    def update(self, instance, validated_data):
        validated_data = self._correct_validated_data(validated_data)

        manual_order = validated_data.pop("manual_order")
        if not manual_order:
            order = validated_data.pop("order", None)
            self._validate_order(
                order, {"alert_receive_channel_id": instance.alert_receive_channel_id, "is_default": False}
            )
            self._change_position(order, instance)

        return super().update(instance, validated_data)


class DefaultChannelFilterSerializer(OrderedModelSerializerMixin, serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    slack = serializers.DictField(required=False)
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
            "escalation_chain_id",
        ]

    def _validate_slack_channel_id(self, slack_channel_id):
        SlackChannel = apps.get_model("slack", "SlackChannel")

        if slack_channel_id is not None:
            slack_channel_id = slack_channel_id.upper()
            organization = self.context["request"].auth.organization
            slack_team_identity = organization.slack_team_identity
            try:
                slack_team_identity.get_cached_channels().get(slack_id=slack_channel_id)
            except SlackChannel.DoesNotExist:
                raise BadRequest(detail="Slack channel does not exist")
        return slack_channel_id

    def _correct_validated_data(self, validated_data):
        slack_field = validated_data.pop("slack", {})
        if "channel_id" in slack_field:
            validated_data["slack_channel_id"] = self._validate_slack_channel_id(slack_field.get("channel_id"))
        return validated_data

    def to_representation(self, instance):
        result = super().to_representation(instance)
        result["slack"] = {"channel_id": instance.slack_channel_id}
        return result

    def update(self, instance, validated_data):
        validated_data = self._correct_validated_data(validated_data)
        return super().update(instance, validated_data)

    def validate_escalation_chain_id(self, escalation_chain):
        if escalation_chain is None:
            return escalation_chain
        if self.instance is not None:
            alert_receive_channel = self.instance.alert_receive_channel
        else:
            alert_receive_channel = AlertReceiveChannel.objects.get(
                public_primary_key=self.initial_data["integration_id"]
            )

        if escalation_chain.team != alert_receive_channel.team:
            raise BadRequest(detail="Escalation chain must be assigned to the same team as the integration")

        return escalation_chain
