from collections import defaultdict
from http.client import responses

from django.core.validators import URLValidator, ValidationError
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apps.webhooks.models import Webhook
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField
from common.api_helpers.utils import CurrentOrganizationDefault, CurrentTeamDefault, CurrentUserDefault
from common.jinja_templater import apply_jinja_template
from common.jinja_templater.apply_jinja_template import JinjaTemplateError, JinjaTemplateWarning


class WebhookSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    organization = serializers.HiddenField(default=CurrentOrganizationDefault())
    team = TeamPrimaryKeyRelatedField(allow_null=True, default=CurrentTeamDefault())
    user = serializers.HiddenField(default=CurrentUserDefault())
    last_run = serializers.SerializerMethodField()
    forward_all = serializers.BooleanField(allow_null=True, required=False)

    class Meta:
        model = Webhook
        fields = [
            "id",
            "name",
            "team",
            "data",
            "user",
            "username",
            "password",
            "authorization_header",
            "organization",
            "trigger_template",
            "headers",
            "url",
            "data",
            "forward_all",
            "http_method",
            "trigger_type",
            "last_run",
        ]
        extra_kwargs = {
            "authorization_header": {"write_only": True},
            "name": {"required": True, "allow_null": False, "allow_blank": False},
            "password": {"write_only": True},
            "url": {"required": True, "allow_null": False, "allow_blank": False},
        }

        validators = [UniqueTogetherValidator(queryset=Webhook.objects.all(), fields=["name", "organization"])]

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
            apply_jinja_template(data, alert_payload=defaultdict(str), alert_group_id="abcd")
        except JinjaTemplateError as e:
            raise serializers.ValidationError(e.fallback_message)
        except JinjaTemplateWarning:
            # Suppress render exceptions since we do not have a representative payload to test with
            pass

        return data

    def validate_forward_all(self, data):
        if data is None:
            return False
        return data

    def get_last_run(self, obj):
        last_run = ""
        last_log = obj.logs.all().last()
        if last_log:
            last_run = last_log.last_run_at.strftime("%Y-%m-%dT%H:%M:%SZ")
            if last_log.response_status:
                reason = responses[int(last_log.response_status)]
                last_run += " ({} {})".format(last_log.response_status, reason)
        return last_run
