from collections import OrderedDict

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError as DjangoValidationError
from django.template.loader import render_to_string
from jinja2 import TemplateSyntaxError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField, set_value

from apps.alerts.grafana_alerting_sync_manager.grafana_alerting_sync import GrafanaAlertingSyncManager
from apps.alerts.models import AlertReceiveChannel
from apps.base.messaging import get_messaging_backends
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import APPEARANCE_TEMPLATE_NAMES, EagerLoadingMixin
from common.api_helpers.utils import CurrentTeamDefault
from common.jinja_templater import apply_jinja_template, jinja_template_env
from common.jinja_templater.apply_jinja_template import JinjaTemplateWarning

from .integration_heartbeat import IntegrationHeartBeatSerializer


def valid_jinja_template_for_serializer_method_field(template):
    for _, val in template.items():
        try:
            apply_jinja_template(val, payload={})
        except JinjaTemplateWarning:
            # Suppress warnings, template may be valid with payload
            pass


class AlertReceiveChannelSerializer(EagerLoadingMixin, serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    integration_url = serializers.ReadOnlyField()
    alert_count = serializers.SerializerMethodField()
    alert_groups_count = serializers.SerializerMethodField()
    author = serializers.CharField(read_only=True, source="author.public_primary_key")
    organization = serializers.CharField(read_only=True, source="organization.public_primary_key")
    team = TeamPrimaryKeyRelatedField(allow_null=True, default=CurrentTeamDefault())
    is_able_to_autoresolve = serializers.ReadOnlyField()
    default_channel_filter = serializers.SerializerMethodField()
    instructions = serializers.SerializerMethodField()
    demo_alert_enabled = serializers.BooleanField(source="is_demo_alert_enabled", read_only=True)
    maintenance_till = serializers.ReadOnlyField(source="till_maintenance_timestamp")
    heartbeat = serializers.SerializerMethodField()
    allow_delete = serializers.SerializerMethodField()
    description_short = serializers.CharField(max_length=250, required=False)
    demo_alert_payload = serializers.SerializerMethodField()

    # integration heartbeat is in PREFETCH_RELATED not by mistake.
    # With using of select_related ORM builds strange join
    # which leads to incorrect heartbeat-alert_receive_channel binding in result
    PREFETCH_RELATED = ["channel_filters", "integration_heartbeat"]
    SELECT_RELATED = ["organization", "author"]

    class Meta:
        model = AlertReceiveChannel
        fields = [
            "id",
            "description",
            "description_short",
            "integration",
            "smile_code",
            "verbal_name",
            "author",
            "organization",
            "team",
            "created_at",
            "integration_url",
            "alert_count",
            "alert_groups_count",
            "allow_source_based_resolving",
            "instructions",
            "is_able_to_autoresolve",
            "default_channel_filter",
            "demo_alert_enabled",
            "maintenance_mode",
            "maintenance_till",
            "heartbeat",
            "is_available_for_integration_heartbeat",
            "allow_delete",
            "demo_alert_payload",
        ]
        read_only_fields = [
            "created_at",
            "author",
            "organization",
            "smile_code",
            "integration_url",
            "instructions",
            "demo_alert_enabled",
            "maintenance_mode",
            "demo_alert_payload",
        ]
        extra_kwargs = {"integration": {"required": True}}

    def create(self, validated_data):
        organization = self.context["request"].auth.organization
        integration = validated_data.get("integration")
        if integration == AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING:
            connection_error = GrafanaAlertingSyncManager.check_for_connection_errors(organization)
            if connection_error:
                raise BadRequest(detail=connection_error)
        instance = AlertReceiveChannel.create(
            **validated_data, organization=organization, author=self.context["request"].user
        )

        return instance

    def get_instructions(self, obj):
        if obj.integration in [AlertReceiveChannel.INTEGRATION_MAINTENANCE]:
            return ""

        rendered_instruction_for_web = render_to_string(
            AlertReceiveChannel.INTEGRATIONS_TO_INSTRUCTIONS_WEB[obj.integration], {"alert_receive_channel": obj}
        )

        return rendered_instruction_for_web

    # MethodFields are used instead of relevant properties because of properties hit db on each instance in queryset
    def get_default_channel_filter(self, obj):
        for filter in obj.channel_filters.all():
            if filter.is_default:
                return filter.public_primary_key

    def validate_verbal_name(self, verbal_name):
        organization = self.context["request"].auth.organization
        if verbal_name is None or (self.instance and verbal_name == self.instance.verbal_name):
            return verbal_name
        try:
            obj = AlertReceiveChannel.objects.get(organization=organization, verbal_name=verbal_name)
        except AlertReceiveChannel.DoesNotExist:
            return verbal_name
        if self.instance and obj.id == self.instance.id:
            return verbal_name
        else:
            raise serializers.ValidationError(detail="Integration with this name already exists")

    def get_heartbeat(self, obj):
        try:
            heartbeat = obj.integration_heartbeat
        except ObjectDoesNotExist:
            return None
        return IntegrationHeartBeatSerializer(heartbeat).data

    def get_allow_delete(self, obj):
        return True

    def get_alert_count(self, obj):
        return 0

    def get_alert_groups_count(self, obj):
        return 0

    def get_demo_alert_payload(self, obj):
        if obj.is_demo_alert_enabled:
            try:
                return obj.config.example_payload
            except AttributeError:
                return "{}"
        return None


class AlertReceiveChannelUpdateSerializer(AlertReceiveChannelSerializer):
    class Meta(AlertReceiveChannelSerializer.Meta):
        read_only_fields = [*AlertReceiveChannelSerializer.Meta.read_only_fields, "integration"]


class FastAlertReceiveChannelSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    integration = serializers.CharField(read_only=True)
    deleted = serializers.SerializerMethodField()

    class Meta:
        model = AlertReceiveChannel
        fields = ["id", "integration", "verbal_name", "deleted"]

    def get_deleted(self, obj):
        # Treat direct paging integrations as deleted, so integration settings are disabled on the frontend
        return obj.deleted_at is not None or obj.integration == AlertReceiveChannel.INTEGRATION_DIRECT_PAGING


class FilterAlertReceiveChannelSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = AlertReceiveChannel
        fields = ["value", "display_name"]

    def get_value(self, obj):
        return obj.public_primary_key

    def get_display_name(self, obj):
        display_name = obj.verbal_name or AlertReceiveChannel.INTEGRATION_CHOICES[obj.integration][1]
        return display_name


class AlertReceiveChannelTemplatesSerializer(EagerLoadingMixin, serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    CORE_TEMPLATE_NAMES = [
        "slack_title_template",
        "slack_message_template",
        "slack_image_url_template",
        "web_title_template",
        "web_message_template",
        "web_image_url_template",
        "telegram_title_template",
        "telegram_message_template",
        "telegram_image_url_template",
        "sms_title_template",
        "phone_call_title_template",
        "source_link_template",
        "grouping_id_template",
        "resolve_condition_template",
        "acknowledge_condition_template",
    ]

    payload_example = SerializerMethodField()
    is_based_on_alertmanager = SerializerMethodField()

    class Meta:
        model = AlertReceiveChannel
        fields = [
            "id",
            "verbal_name",
            "payload_example",
            "is_based_on_alertmanager",
        ]
        extra_kwargs = {"integration": {"required": True}}

    def get_payload_example(self, obj):
        AlertGroup = apps.get_model("alerts", "AlertGroup")
        if "alert_group_id" in self.context["request"].query_params:
            alert_group_id = self.context["request"].query_params.get("alert_group_id")
            try:
                return obj.alert_groups.get(public_primary_key=alert_group_id).alerts.first().raw_request_data
            except AlertGroup.DoesNotExist:
                raise serializers.ValidationError("Alert group doesn't exist for this integration")
            except AttributeError:
                raise serializers.ValidationError("Unable to retrieve example payload for this alert group")
        else:
            try:
                return obj.alert_groups.last().alerts.first().raw_request_data
            except AttributeError:
                return None

    def get_is_based_on_alertmanager(self, obj):
        return obj.has_alertmanager_payload_structure

    # Override method to pass field_name directly in set_value to handle None values for WritableSerializerField
    def to_internal_value(self, data):
        """
        Dict of native values <- Dict of primitive datatypes.
        """
        # First validate and save data from serializer fields
        ret = super().to_internal_value(data)

        # Separately validate and save template fields we generate dynamically
        errors = OrderedDict()

        # handle updates for core templates
        core_template_errors = self._handle_core_template_updates(data, ret)
        errors.update(core_template_errors)

        # handle updates for messaging backend templates
        messaging_backend_errors = self._handle_messaging_backend_updates(data, ret)
        errors.update(messaging_backend_errors)

        if errors:
            raise ValidationError(errors)
        return ret

    def _handle_messaging_backend_updates(self, data, ret):
        """Update additional messaging backend templates if needed."""
        errors = {}
        for backend_id, backend in get_messaging_backends():
            if not backend.customizable_templates:
                continue
            # fetch existing templates if any
            backend_templates = {}
            if self.instance.messaging_backends_templates is not None:
                backend_templates = self.instance.messaging_backends_templates.get(backend_id, {})
            # validate updated templates if any
            backend_updates = {}
            for field in APPEARANCE_TEMPLATE_NAMES:
                field_name = f"{backend.slug}_{field}_template"
                value = data.get(field_name)
                validator = jinja_template_env.from_string
                if value is not None:
                    try:
                        if value:
                            validator(value)
                    except TemplateSyntaxError:
                        errors[field_name] = "invalid template"
                    except DjangoValidationError:
                        errors[field_name] = "invalid URL"
                    else:
                        backend_updates[field] = value
            # update backend templates
            backend_templates.update(backend_updates)
            set_value(ret, ["messaging_backends_templates", backend_id], backend_templates)

        return errors

    def _handle_core_template_updates(self, data, ret):
        """Update core templates if needed."""
        errors = {}

        core_template_names = self.CORE_TEMPLATE_NAMES

        for field_name in core_template_names:
            value = data.get(field_name)
            validator = jinja_template_env.from_string
            if value is not None:
                try:
                    if value:
                        validator(value)
                except TemplateSyntaxError:
                    errors[field_name] = "invalid template"
                except DjangoValidationError:
                    errors[field_name] = "invalid URL"
                set_value(ret, [field_name], value)
        return errors

    def to_representation(self, obj):
        ret = super().to_representation(obj)
        ret = self._get_templates_to_show(ret)

        core_templates = self._get_core_templates(obj)
        ret.update(core_templates)

        # include messaging backend templates
        additional_templates = self._get_messaging_backend_templates(obj)
        ret.update(additional_templates)

        return ret

    def _get_templates_to_show(self, response_data):
        """
        For On-prem installations with disabled features it is needed to disable corresponding templates
        """
        slack_integration_required_templates = [
            "slack_title_template",
            "slack_message_template",
            "slack_image_url_template",
        ]
        telegram_integration_required_templates = [
            "telegram_title_template",
            "telegram_message_template",
            "telegram_image_url_template",
        ]
        if not settings.FEATURE_SLACK_INTEGRATION_ENABLED:
            for st in slack_integration_required_templates:
                response_data.pop(st)
        if not settings.FEATURE_TELEGRAM_INTEGRATION_ENABLED:
            for tt in telegram_integration_required_templates:
                response_data.pop(tt)

        return response_data

    def _get_messaging_backend_templates(self, obj):
        """Return additional messaging backend templates if any."""
        templates = {}
        for backend_id, backend in get_messaging_backends():
            if not backend.customizable_templates:
                continue
            for field in backend.template_fields:
                value = None
                is_default = False
                if obj.messaging_backends_templates:
                    value = obj.messaging_backends_templates.get(backend_id, {}).get(field)
                if not value:
                    value = obj.get_default_template_attribute(backend_id, field)
                    is_default = True
                field_name = f"{backend.slug}_{field}_template"
                templates[field_name] = value
                templates[f"{field_name}_is_default"] = is_default
        return templates

    def _get_core_templates(self, obj):
        core_templates = {}

        core_template_names = self.CORE_TEMPLATE_NAMES
        for template_name in core_template_names:
            template_value = getattr(obj, template_name)
            defaults = getattr(obj, f"INTEGRATION_TO_DEFAULT_{template_name.upper()}", {})
            default_template_value = defaults.get(obj.integration)
            core_templates[template_name] = template_value or default_template_value
            core_templates[f"{template_name}_is_default"] = not bool(template_value)

        return core_templates
