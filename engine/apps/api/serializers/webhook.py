from collections import defaultdict
from http.client import responses

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apps.webhooks.models import Webhook, WebhookLog
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField
from common.api_helpers.utils import CurrentOrganizationDefault, CurrentTeamDefault, CurrentUserDefault
from common.jinja_templater import apply_jinja_template
from common.jinja_templater.apply_jinja_template import JinjaTemplateError, JinjaTemplateWarning


class WebhookLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookLog
        fields = [
            "last_run_at",
            "input_data",
            "url",
            "trigger",
            "headers",
            "data",
            "response_status",
            "response",
        ]


class WebhookSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    organization = serializers.HiddenField(default=CurrentOrganizationDefault())
    team = TeamPrimaryKeyRelatedField(allow_null=True, default=CurrentTeamDefault())
    user = serializers.HiddenField(default=CurrentUserDefault())
    last_run = serializers.SerializerMethodField()
    trigger_type = serializers.CharField(required=True)
    forward_all = serializers.BooleanField(allow_null=True, required=False)
    last_status_log = serializers.SerializerMethodField()
    trigger_type_name = serializers.SerializerMethodField()

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
            "trigger_type_name",
            "last_run",
            "last_status_log",
        ]
        extra_kwargs = {
            "authorization_header": {"write_only": True},
            "name": {"required": True, "allow_null": False, "allow_blank": False},
            "password": {"write_only": True},
            "url": {"required": True, "allow_null": False, "allow_blank": False},
        }

        validators = [UniqueTogetherValidator(queryset=Webhook.objects.all(), fields=["name", "organization"])]

    def _validate_template_field(self, template):
        try:
            apply_jinja_template(template, alert_payload=defaultdict(str), alert_group_id="alert_group_1")
        except JinjaTemplateError as e:
            raise serializers.ValidationError(e.fallback_message)
        except JinjaTemplateWarning:
            # Suppress render exceptions since we do not have a representative payload to test with
            pass
        return template

    def validate_trigger_template(self, trigger_template):
        if not trigger_template:
            return None
        return self._validate_template_field(trigger_template)

    def validate_headers(self, headers):
        if not headers:
            return None
        return self._validate_template_field(headers)

    def validate_url(self, url):
        if not url:
            return None
        return self._validate_template_field(url)

    def validate_data(self, data):
        if not data:
            return None
        return self._validate_template_field(data)

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

    def get_last_status_log(self, obj):
        return WebhookLogSerializer(obj.logs.all().last()).data

    def get_trigger_type_name(self, obj):
        trigger_type_name = ""
        if obj.trigger_type:
            trigger_type_name = Webhook.TRIGGER_TYPES[int(obj.trigger_type)][1]
        return trigger_type_name
