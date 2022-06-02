import json

from django.core.validators import URLValidator, ValidationError
from jinja2 import Template, TemplateError
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apps.alerts.models import CustomButton
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField
from common.api_helpers.utils import CurrentOrganizationDefault, CurrentTeamDefault


class CustomButtonSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    organization = serializers.HiddenField(default=CurrentOrganizationDefault())
    team = TeamPrimaryKeyRelatedField(allow_null=True, default=CurrentTeamDefault())
    forward_whole_payload = serializers.BooleanField(allow_null=True, required=False)

    class Meta:
        model = CustomButton
        fields = [
            "id",
            "name",
            "team",
            "webhook",
            "data",
            "user",
            "password",
            "authorization_header",
            "organization",
            "forward_whole_payload",
        ]
        extra_kwargs = {
            "name": {"required": True, "allow_null": False, "allow_blank": False},
            "webhook": {"required": True, "allow_null": False, "allow_blank": False},
        }

        validators = [UniqueTogetherValidator(queryset=CustomButton.objects.all(), fields=["name", "organization"])]

    def validate_webhook(self, webhook):
        if webhook:
            try:
                URLValidator()(webhook)
            except ValidationError:
                raise serializers.ValidationError("Webhook is incorrect")
            return webhook
        return None

    def validate_data(self, data):
        if not data:
            return None

        try:
            json.loads(data)
        except ValueError:
            raise serializers.ValidationError("Data has incorrect format")

        try:
            Template(data)
        except TemplateError:
            raise serializers.ValidationError("Data has incorrect template")

        return data

    def validate_forward_whole_payload(self, data):
        if data is None:
            return False
        return data
