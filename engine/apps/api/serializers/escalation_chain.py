from rest_framework import serializers

from apps.alerts.models import EscalationChain
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField
from common.api_helpers.utils import CurrentOrganizationDefault, CurrentTeamDefault


class EscalationChainSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    organization = serializers.HiddenField(default=CurrentOrganizationDefault())
    team = TeamPrimaryKeyRelatedField(allow_null=True, default=CurrentTeamDefault())

    class Meta:
        model = EscalationChain
        fields = ("id", "name", "organization", "team")


class EscalationChainListSerializer(EscalationChainSerializer):
    number_of_integrations = serializers.SerializerMethodField()
    number_of_routes = serializers.SerializerMethodField()

    class Meta(EscalationChainSerializer.Meta):
        fields = [*EscalationChainSerializer.Meta.fields, "number_of_integrations", "number_of_routes"]

    def get_number_of_integrations(self, obj):
        # num_integrations param added in queryset via annotate. Check EscalationChainViewSet.get_queryset
        return getattr(obj, "num_integrations")

    def get_number_of_routes(self, obj):
        # num_routes param added in queryset via annotate. Check EscalationChainViewSet.get_queryset
        return getattr(obj, "num_routes")


class FilterEscalationChainSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source="public_primary_key")
    display_name = serializers.CharField(source="name")

    class Meta:
        model = EscalationChain
        fields = ["value", "display_name"]
