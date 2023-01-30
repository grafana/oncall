from collections import OrderedDict
from collections.abc import Mapping

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import URLValidator
from django.template.loader import render_to_string
from django.utils import timezone
from jinja2 import TemplateSyntaxError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField, SkipField, get_error_detail, set_value
from rest_framework.settings import api_settings

from apps.alerts.grafana_alerting_sync_manager.grafana_alerting_sync import GrafanaAlertingSyncManager
from apps.alerts.models import AlertReceiveChannel
from apps.base.messaging import get_messaging_backends
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField, WritableSerializerMethodField
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import IMAGE_URL, TEMPLATE_NAMES_ONLY_WITH_NOTIFICATION_CHANNEL, EagerLoadingMixin
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
    slack_title_template = WritableSerializerMethodField(
        allow_null=True,
        deserializer_field=serializers.CharField(),
        validators=[valid_jinja_template_for_serializer_method_field],
        required=False,
    )
    slack_message_template = WritableSerializerMethodField(
        allow_null=True,
        deserializer_field=serializers.CharField(),
        validators=[valid_jinja_template_for_serializer_method_field],
        required=False,
    )
    slack_image_url_template = WritableSerializerMethodField(
        allow_null=True,
        deserializer_field=serializers.CharField(),
        validators=[valid_jinja_template_for_serializer_method_field],
        required=False,
    )
    web_title_template = WritableSerializerMethodField(
        allow_null=True,
        deserializer_field=serializers.CharField(),
        validators=[valid_jinja_template_for_serializer_method_field],
        required=False,
    )
    web_message_template = WritableSerializerMethodField(
        allow_null=True,
        deserializer_field=serializers.CharField(),
        validators=[valid_jinja_template_for_serializer_method_field],
        required=False,
    )
    web_image_url_template = WritableSerializerMethodField(
        allow_null=True,
        deserializer_field=serializers.CharField(),
        validators=[valid_jinja_template_for_serializer_method_field],
        required=False,
    )
    sms_title_template = WritableSerializerMethodField(
        allow_null=True,
        deserializer_field=serializers.CharField(),
        validators=[valid_jinja_template_for_serializer_method_field],
        required=False,
    )
    phone_call_title_template = WritableSerializerMethodField(
        allow_null=True,
        deserializer_field=serializers.CharField(),
        validators=[valid_jinja_template_for_serializer_method_field],
        required=False,
    )
    telegram_title_template = WritableSerializerMethodField(
        allow_null=True,
        deserializer_field=serializers.CharField(),
        validators=[valid_jinja_template_for_serializer_method_field],
        required=False,
    )
    telegram_message_template = WritableSerializerMethodField(
        allow_null=True,
        deserializer_field=serializers.CharField(),
        validators=[valid_jinja_template_for_serializer_method_field],
        required=False,
    )
    telegram_image_url_template = WritableSerializerMethodField(
        allow_null=True,
        deserializer_field=serializers.CharField(),
        validators=[valid_jinja_template_for_serializer_method_field],
        required=False,
    )
    source_link_template = WritableSerializerMethodField(
        allow_null=True,
        deserializer_field=serializers.CharField(),
        validators=[valid_jinja_template_for_serializer_method_field],
        required=False,
    )
    grouping_id_template = WritableSerializerMethodField(
        allow_null=True,
        deserializer_field=serializers.CharField(),
        validators=[valid_jinja_template_for_serializer_method_field],
        required=False,
    )
    acknowledge_condition_template = WritableSerializerMethodField(
        allow_null=True,
        deserializer_field=serializers.CharField(),
        validators=[valid_jinja_template_for_serializer_method_field],
        required=False,
    )
    resolve_condition_template = WritableSerializerMethodField(
        allow_null=True,
        deserializer_field=serializers.CharField(),
        validators=[valid_jinja_template_for_serializer_method_field],
        required=False,
    )

    payload_example = SerializerMethodField()

    class Meta:
        model = AlertReceiveChannel
        fields = [
            "id",
            "verbal_name",
            "slack_title_template",
            "slack_message_template",
            "slack_image_url_template",
            "sms_title_template",
            "phone_call_title_template",
            "web_title_template",
            "web_message_template",
            "web_image_url_template",
            "telegram_title_template",
            "telegram_message_template",
            "telegram_image_url_template",
            "source_link_template",
            "grouping_id_template",
            "resolve_condition_template",
            "payload_example",
            "acknowledge_condition_template",
        ]
        extra_kwargs = {"integration": {"required": True}}

    # MethodFields are used instead of relevant properties because of properties hit db on each instance in queryset

    def get_slack_title_template(self, obj):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_SLACK_TITLE_TEMPLATE[obj.integration]
        return obj.slack_title_template or default_template

    def set_slack_title_template(self, value):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_SLACK_TITLE_TEMPLATE[self.instance.integration]
        if default_template is None or default_template.strip() != value.strip():
            self.instance.slack_title_template = value.strip()
        elif default_template is not None and default_template.strip() == value.strip():
            self.instance.slack_title_template = None

    def get_slack_message_template(self, obj):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_SLACK_MESSAGE_TEMPLATE[obj.integration]
        return obj.slack_message_template or default_template

    def set_slack_message_template(self, value):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_SLACK_MESSAGE_TEMPLATE[self.instance.integration]
        if default_template is None or default_template.strip() != value.strip():
            self.instance.slack_message_template = value.strip()
        elif default_template is not None and default_template.strip() == value.strip():
            self.instance.slack_message_template = None

    def get_slack_image_url_template(self, obj):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_SLACK_IMAGE_URL_TEMPLATE[obj.integration]
        return obj.slack_image_url_template or default_template

    def set_slack_image_url_template(self, value):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_SLACK_IMAGE_URL_TEMPLATE[
            self.instance.integration
        ]
        if default_template is None or default_template.strip() != value.strip():
            self.instance.slack_image_url_template = value.strip()
        elif default_template is not None and default_template.strip() == value.strip():
            self.instance.slack_image_url_template = None

    def get_sms_title_template(self, obj):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_SMS_TITLE_TEMPLATE[obj.integration]
        return obj.sms_title_template or default_template

    def set_sms_title_template(self, value):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_SMS_TITLE_TEMPLATE[self.instance.integration]
        if default_template is None or default_template.strip() != value.strip():
            self.instance.sms_title_template = value.strip()
        elif default_template is not None and default_template.strip() == value.strip():
            self.instance.sms_title_template = None

    def get_phone_call_title_template(self, obj):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_PHONE_CALL_TITLE_TEMPLATE[obj.integration]
        return obj.phone_call_title_template or default_template

    def set_phone_call_title_template(self, value):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_PHONE_CALL_TITLE_TEMPLATE[
            self.instance.integration
        ]
        if default_template is None or default_template.strip() != value.strip():
            self.instance.phone_call_title_template = value.strip()
        elif default_template is not None and default_template.strip() == value.strip():
            self.instance.phone_call_title_template = None

    def get_web_title_template(self, obj):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_WEB_TITLE_TEMPLATE[obj.integration]
        return obj.web_title_template or default_template

    def set_web_title_template(self, value):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_WEB_TITLE_TEMPLATE[self.instance.integration]
        if default_template is None or default_template.strip() != value.strip():
            self.instance.web_title_template = value.strip()
        elif default_template is not None and default_template.strip() == value.strip():
            self.instance.web_title_template = None
        self.instance.web_templates_modified_at = timezone.now()

    def get_web_message_template(self, obj):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_WEB_MESSAGE_TEMPLATE[obj.integration]
        return obj.web_message_template or default_template

    def set_web_message_template(self, value):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_WEB_MESSAGE_TEMPLATE[self.instance.integration]
        if default_template is None or default_template.strip() != value.strip():
            self.instance.web_message_template = value.strip()
        elif default_template is not None and default_template.strip() == value.strip():
            self.instance.web_message_template = None
        self.instance.web_templates_modified_at = timezone.now()

    def get_web_image_url_template(self, obj):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_WEB_IMAGE_URL_TEMPLATE[obj.integration]
        return obj.web_image_url_template or default_template

    def set_web_image_url_template(self, value):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_WEB_IMAGE_URL_TEMPLATE[self.instance.integration]
        if default_template is None or default_template.strip() != value.strip():
            self.instance.web_image_url_template = value.strip()
        elif default_template is not None and default_template.strip() == value.strip():
            self.instance.web_image_url_template = None
        self.instance.web_templates_modified_at = timezone.now()

    def get_telegram_title_template(self, obj):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_TELEGRAM_TITLE_TEMPLATE[obj.integration]
        return obj.telegram_title_template or default_template

    def set_telegram_title_template(self, value):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_TELEGRAM_TITLE_TEMPLATE[self.instance.integration]
        if default_template is None or default_template.strip() != value.strip():
            self.instance.telegram_title_template = value.strip()
        elif default_template is not None and default_template.strip() == value.strip():
            self.instance.telegram_title_template = None

    def get_telegram_message_template(self, obj):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_TELEGRAM_MESSAGE_TEMPLATE[obj.integration]
        return obj.telegram_message_template or default_template

    def set_telegram_message_template(self, value):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_TELEGRAM_MESSAGE_TEMPLATE[
            self.instance.integration
        ]
        if default_template is None or default_template.strip() != value.strip():
            self.instance.telegram_message_template = value.strip()
        elif default_template is not None and default_template.strip() == value.strip():
            self.instance.telegram_message_template = None

    def get_telegram_image_url_template(self, obj):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_TELEGRAM_IMAGE_URL_TEMPLATE[obj.integration]
        return obj.telegram_image_url_template or default_template

    def set_telegram_image_url_template(self, value):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_TELEGRAM_IMAGE_URL_TEMPLATE[
            self.instance.integration
        ]
        if default_template is None or default_template.strip() != value.strip():
            self.instance.telegram_image_url_template = value.strip()
        elif default_template is not None and default_template.strip() == value.strip():
            self.instance.telegram_image_url_template = None

    def get_source_link_template(self, obj):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_SOURCE_LINK_TEMPLATE[obj.integration]
        return obj.source_link_template or default_template

    def set_source_link_template(self, value):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_SOURCE_LINK_TEMPLATE[self.instance.integration]
        if default_template is None or default_template.strip() != value.strip():
            self.instance.source_link_template = value.strip()
        elif default_template is not None and default_template.strip() == value.strip():
            self.instance.source_link_template = None

    def get_grouping_id_template(self, obj):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_GROUPING_ID_TEMPLATE[obj.integration]
        return obj.grouping_id_template or default_template

    def set_grouping_id_template(self, value):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_GROUPING_ID_TEMPLATE[self.instance.integration]
        if default_template is None or default_template.strip() != value.strip():
            self.instance.grouping_id_template = value.strip()
        elif default_template is not None and default_template.strip() == value.strip():
            self.instance.grouping_id_template = None

    def get_acknowledge_condition_template(self, obj):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_ACKNOWLEDGE_CONDITION_TEMPLATE[obj.integration]
        return obj.acknowledge_condition_template or default_template

    def set_acknowledge_condition_template(self, value):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_ACKNOWLEDGE_CONDITION_TEMPLATE[
            self.instance.integration
        ]
        if default_template is None or default_template.strip() != value.strip():
            self.instance.acknowledge_condition_template = value.strip()
        elif default_template is not None and default_template.strip() == value.strip():
            self.instance.acknowledge_condition_template = None

    def get_resolve_condition_template(self, obj):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_RESOLVE_CONDITION_TEMPLATE[obj.integration]
        return obj.resolve_condition_template or default_template

    def set_resolve_condition_template(self, value):
        default_template = AlertReceiveChannel.INTEGRATION_TO_DEFAULT_RESOLVE_CONDITION_TEMPLATE[
            self.instance.integration
        ]
        if default_template is None or default_template.strip() != value.strip():
            self.instance.resolve_condition_template = value.strip()
        elif default_template is not None and default_template.strip() == value.strip():
            self.instance.resolve_condition_template = None

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

    # Override method to pass field_name directly in set_value to handle None values for WritableSerializerField
    def to_internal_value(self, data):
        """
        Dict of native values <- Dict of primitive datatypes.
        """
        if not isinstance(data, Mapping):
            message = self.error_messages["invalid"].format(datatype=type(data).__name__)
            raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [message]}, code="invalid")

        ret = OrderedDict()
        errors = OrderedDict()
        fields = self._writable_fields

        for field in fields:
            validate_method = getattr(self, "validate_" + field.field_name, None)
            primitive_value = field.get_value(data)
            try:
                validated_value = field.run_validation(primitive_value)
                if validate_method is not None:
                    validated_value = validate_method(validated_value)
            except ValidationError as exc:
                errors[field.field_name] = exc.detail
            except DjangoValidationError as exc:
                errors[field.field_name] = get_error_detail(exc)
            except SkipField:
                pass
            else:
                # Line because of which method is overriden
                if validated_value is None and isinstance(field, WritableSerializerMethodField):
                    set_value(ret, [field.field_name], validated_value)
                else:
                    set_value(ret, field.source_attrs, validated_value)

        # handle updates for messaging backend templates
        messaging_backend_errors = self._handle_messaging_backend_updates(data, ret)
        errors.update(messaging_backend_errors)

        if errors:
            raise ValidationError(errors)

        return ret

    def _handle_messaging_backend_updates(self, data, ret):
        """Update additional messaging backend templates if needed."""
        errors = {}
        for backend_id, _ in get_messaging_backends():
            # fetch existing templates if any
            backend_templates = {}
            if self.instance.messaging_backends_templates is not None:
                backend_templates = self.instance.messaging_backends_templates.get(backend_id, {})
            # validate updated templates if any
            backend_updates = {}
            for field in TEMPLATE_NAMES_ONLY_WITH_NOTIFICATION_CHANNEL:
                field_name = f"{backend_id.lower()}_{field}_template"
                value = data.get(field_name)
                validator = jinja_template_env.from_string if field != IMAGE_URL else URLValidator()
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

    def to_representation(self, obj):
        ret = super().to_representation(obj)
        ret = self._get_templates_to_show(ret)

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
            for field in backend.template_fields:
                value = None
                if obj.messaging_backends_templates:
                    value = obj.messaging_backends_templates.get(backend_id, {}).get(field)
                if value is None:
                    value = obj.get_default_template_attribute(backend_id, field)
                field_name = f"{backend_id.lower()}_{field}_template"
                templates[field_name] = value
        return templates
