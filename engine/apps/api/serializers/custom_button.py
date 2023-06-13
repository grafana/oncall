from collections import defaultdict

from django.core.validators import URLValidator, ValidationError
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apps.alerts.models import CustomButton
from apps.base.utils import live_settings
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField
from common.api_helpers.utils import CurrentOrganizationDefault, CurrentTeamDefault, URLValidatorWithoutTLD
from common.jinja_templater import apply_jinja_template
from common.jinja_templater.apply_jinja_template import JinjaTemplateError, JinjaTemplateWarning


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
                if live_settings.DANGEROUS_WEBHOOKS_ENABLED:
                    URLValidatorWithoutTLD()(webhook)
                else:
                    URLValidator()(webhook)
            except ValidationError:
                raise serializers.ValidationError("Webhook is incorrect")
            return webhook
        return None

    def validate_data(self, data):
        if not data:
            return None

        try:
            apply_jinja_template(data, alert_payload=defaultdict(str), alert_group_id="abcd")
        except JinjaTemplateError as e:
            raise serializers.ValidationError(e.fallback_message)
        except JinjaTemplateWarning:
            # Suppress render exceptions since we do not have a representative payload to test with
            pass

        return data

    def validate_forward_whole_payload(self, data):
        if data is None:
            return False
        return data
