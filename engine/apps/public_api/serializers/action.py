import json

from django.core.validators import URLValidator, ValidationError
from jinja2 import Template, TemplateError
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apps.alerts.models import CustomButton
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField
from common.api_helpers.utils import CurrentOrganizationDefault


class ActionCreateSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    organization = serializers.HiddenField(default=CurrentOrganizationDefault())
    team_id = TeamPrimaryKeyRelatedField(required=False, allow_null=True, source="team")
    url = serializers.CharField(required=True, allow_null=False, allow_blank=False, source="webhook")

    class Meta:
        model = CustomButton
        fields = [
            "id",
            "name",
            "organization",
            "team_id",
            "url",
            "data",
            "user",
            "password",
            "authorization_header",
            "forward_whole_payload",
        ]
        extra_kwargs = {
            "name": {"required": True, "allow_null": False, "allow_blank": False},
            "data": {"required": False, "allow_null": True, "allow_blank": False},
            "user": {"required": False, "allow_null": True, "allow_blank": False},
            "password": {"required": False, "allow_null": True, "allow_blank": False},
            "authorization_header": {"required": False, "allow_null": True, "allow_blank": False},
            "forward_whole_payload": {"required": False, "allow_null": True},
        }

        validators = [UniqueTogetherValidator(queryset=CustomButton.objects.all(), fields=["name", "organization"])]

    def validate_url(self, url):
        if url:
            try:
                URLValidator()(url)
            except ValidationError:
                raise serializers.ValidationError("URL is incorrect")
            return url
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


class ActionUpdateSerializer(ActionCreateSerializer):
    team_id = TeamPrimaryKeyRelatedField(source="team", read_only=True)
    url = serializers.CharField(required=False, allow_null=False, allow_blank=False, source="webhook")

    class Meta(ActionCreateSerializer.Meta):

        extra_kwargs = {
            "name": {"required": False, "allow_null": False, "allow_blank": False},
            "data": {"required": False, "allow_null": True, "allow_blank": False},
            "user": {"required": False, "allow_null": True, "allow_blank": False},
            "password": {"required": False, "allow_null": True, "allow_blank": False},
            "authorization_header": {"required": False, "allow_null": True, "allow_blank": False},
            "forward_whole_payload": {"required": False, "allow_null": True},
        }
