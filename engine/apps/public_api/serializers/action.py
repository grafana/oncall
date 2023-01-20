import json
from collections import defaultdict

from django.core.validators import URLValidator, ValidationError
from jinja2 import TemplateError
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apps.alerts.models import CustomButton
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField
from common.api_helpers.utils import CurrentOrganizationDefault
from common.jinja_templater import jinja_template_env


class HeadersField(serializers.Field):
    """
    The `headers` of a custom button.

    This is a list of objects with `name` and `value` keys and string values.
    In the database, this is stored as a JSON string.
    """

    def to_representation(self, value):
        return json.loads(value)

    def to_internal_value(self, data):
        if not data:
            return None

        try:
            assert isinstance(data, list)
            for header in data:
                assert isinstance(header, dict)
                if not isinstance(header.get("name"), str):
                    raise serializers.ValidationError("Header names must be strings")
                if not isinstance(header.get("value"), str):
                    raise serializers.ValidationError("Header values must be strings")
        except (json.JSONDecodeError, AssertionError):
            raise serializers.ValidationError("Headers has incorrect format")

        return json.dumps(data)


class ActionCreateSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    organization = serializers.HiddenField(default=CurrentOrganizationDefault())
    team_id = TeamPrimaryKeyRelatedField(required=False, allow_null=True, source="team")
    url = serializers.CharField(required=True, allow_null=False, allow_blank=False, source="webhook")
    headers = HeadersField(allow_null=True, required=False)

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
            "headers",
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
            template = jinja_template_env.from_string(data)
        except TemplateError:
            raise serializers.ValidationError("Data has incorrect template")

        try:
            rendered = template.render(
                {
                    # Validate that the template can be rendered with a JSON-ish alert payload.
                    # We don't know what the actual payload will be, so we use a defaultdict
                    # so that attribute access within a template will never fail
                    # (provided it's only one level deep - we won't accept templates that attempt
                    # to do nested attribute access).
                    # Every attribute access should return a string to ensure that users are
                    # correctly using `tojson` or wrapping fields in strings.
                    # If we instead used a `defaultdict(dict)` or `defaultdict(lambda: 1)` we
                    # would accidentally accept templates such as `{"name": {{ alert_payload.name }}}`
                    # which would then fail at the true render time due to the
                    # lack of explicit quotes around the template variable; this would render
                    # as `{"name": some_alert_name}` which is not valid JSON.
                    "alert_payload": defaultdict(str),
                    "alert_group_id": "abcd",
                }
            )
            json.loads(rendered)
        except ValueError:
            raise serializers.ValidationError("Data has incorrect format")

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
