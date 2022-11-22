import json
from collections import defaultdict

from django.core.validators import URLValidator, ValidationError
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apps.alerts.models import CustomButton
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField
from common.api_helpers.utils import CurrentOrganizationDefault, CurrentTeamDefault
from common.jinja_templater import apply_jinja_template
from common.jinja_templater.apply_jinja_template import JinjaTemplateRenderException


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
            rendered = apply_jinja_template(
                data, raise_exception=True, alert_payload=defaultdict(str), alert_group_id="abcd"
            )
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
            json.loads(rendered)
        except JinjaTemplateRenderException as e:
            raise serializers.ValidationError(e.fallback_message)
        except ValueError:
            raise serializers.ValidationError(f"Template should result in JSON value: {rendered}")

        return data

    def validate_forward_whole_payload(self, data):
        if data is None:
            return False
        return data
