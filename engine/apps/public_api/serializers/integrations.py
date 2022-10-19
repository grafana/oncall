from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from jinja2 import TemplateSyntaxError
from rest_framework import fields, serializers

from apps.alerts.grafana_alerting_sync_manager.grafana_alerting_sync import GrafanaAlertingSyncManager
from apps.alerts.models import AlertReceiveChannel
from apps.base.messaging import get_messaging_backends
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import NOTIFICATION_CHANNEL_OPTIONS, EagerLoadingMixin
from common.jinja_templater import jinja_template_env
from common.utils import timed_lru_cache

from .integtration_heartbeat import IntegrationHeartBeatSerializer
from .maintenance import MaintainableObjectSerializerMixin
from .routes import DefaultChannelFilterSerializer


class IntegrationTypeField(fields.CharField):
    def to_representation(self, value):
        return AlertReceiveChannel.INTEGRATIONS_TO_REVERSE_URL_MAP[value]

    def to_internal_value(self, data):
        try:
            integration_type = [
                key for key, value in AlertReceiveChannel.INTEGRATIONS_TO_REVERSE_URL_MAP.items() if value == data
            ][0]
        except IndexError:
            raise BadRequest(detail="Invalid integration type")
        return integration_type


class IntegrationSerializer(EagerLoadingMixin, serializers.ModelSerializer, MaintainableObjectSerializerMixin):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    name = serializers.CharField(required=False, source="verbal_name")
    team_id = TeamPrimaryKeyRelatedField(required=False, allow_null=True, source="team")
    link = serializers.ReadOnlyField(source="integration_url")
    type = IntegrationTypeField(source="integration")
    templates = serializers.DictField(required=False)
    default_route = serializers.DictField(required=False)
    heartbeat = serializers.SerializerMethodField()

    PREFETCH_RELATED = ["channel_filters"]
    SELECT_RELATED = ["organization", "integration_heartbeat"]

    class Meta:
        model = AlertReceiveChannel
        fields = MaintainableObjectSerializerMixin.Meta.fields + [
            "id",
            "name",
            "team_id",
            "link",
            "type",
            "default_route",
            "templates",
            "heartbeat",
        ]

    def to_representation(self, instance):
        result = super().to_representation(instance)
        default_route = self._get_default_route_iterative(instance)
        serializer = DefaultChannelFilterSerializer(default_route, context=self.context)
        result["default_route"] = serializer.data

        # add additional templates for messaging backends
        result["templates"].update(self._get_messaging_backend_templates(instance))

        return result

    def create(self, validated_data):
        validated_data = self._correct_validated_data(validated_data)
        default_route_data = validated_data.pop("default_route", None)
        organization = self.context["request"].auth.organization
        integration = validated_data.get("integration")
        if integration == AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING:
            connection_error = GrafanaAlertingSyncManager.check_for_connection_errors(organization)
            if connection_error:
                raise serializers.ValidationError(connection_error)
        with transaction.atomic():
            instance = AlertReceiveChannel.create(
                **validated_data,
                author=self.context["request"].user,
                organization=organization,
            )
            if default_route_data:
                serializer = DefaultChannelFilterSerializer(
                    instance.default_channel_filter, default_route_data, context=self.context
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
        return instance

    def validate(self, attrs):
        organization = self.context["request"].auth.organization
        verbal_name = attrs.get("verbal_name", None)
        if verbal_name is None:
            return attrs
        try:
            obj = AlertReceiveChannel.objects.get(organization=organization, verbal_name=verbal_name)
        except AlertReceiveChannel.DoesNotExist:
            return attrs
        if self.instance and obj.id == self.instance.id:
            return attrs
        else:
            raise BadRequest(detail="Integration with this name already exists")

    def _correct_validated_data(self, validated_data):
        validated_data = self._correct_validated_data_for_messaging_backends(validated_data)

        templates = validated_data.pop("templates", {})
        for template_name, templates_for_notification_channel in templates.items():
            if type(templates_for_notification_channel) is dict:
                for attr, template in templates_for_notification_channel.items():
                    try:
                        validated_data[AlertReceiveChannel.PUBLIC_TEMPLATES_FIELDS[template_name][attr]] = template
                    except KeyError:
                        raise BadRequest(detail="Invalid template data")
            elif type(templates_for_notification_channel) is str:
                try:
                    validated_data[
                        AlertReceiveChannel.PUBLIC_TEMPLATES_FIELDS[template_name]
                    ] = templates_for_notification_channel
                except KeyError:
                    raise BadRequest(detail="Invalid template data")
            elif templates_for_notification_channel is None:
                try:
                    template_to_set_to_default = AlertReceiveChannel.PUBLIC_TEMPLATES_FIELDS[template_name]
                    if type(template_to_set_to_default) is str:
                        validated_data[AlertReceiveChannel.PUBLIC_TEMPLATES_FIELDS[template_name]] = None
                    elif type(template_to_set_to_default) is dict:
                        for key in template_to_set_to_default.keys():
                            validated_data[AlertReceiveChannel.PUBLIC_TEMPLATES_FIELDS[template_name][key]] = None
                except KeyError:
                    raise BadRequest(detail="Invalid template data")

        return validated_data

    def validate_templates(self, templates):
        if not isinstance(templates, dict):
            raise BadRequest(detail="Invalid template data")

        for notification_channel in NOTIFICATION_CHANNEL_OPTIONS:
            template_data = templates.get(notification_channel, {})
            if template_data is None:
                continue
            if not isinstance(template_data, dict):
                raise BadRequest(detail=f"Invalid {notification_channel} template data")
            for attr, attr_template in template_data.items():
                if attr_template is None:
                    continue
                try:
                    jinja_template_env.from_string(attr_template)
                except TemplateSyntaxError:
                    raise BadRequest(detail=f"invalid {notification_channel} {attr} template")

        for common_template in ["resolve_signal", "grouping_key"]:
            template_data = templates.get(common_template, "")
            if template_data is None:
                continue
            if not isinstance(template_data, str):
                raise BadRequest(detail=f"Invalid {common_template} template data")
            try:
                jinja_template_env.from_string(template_data)
            except TemplateSyntaxError:
                raise BadRequest(detail=f"Invalid {common_template} template data")
        return templates

    def _correct_validated_data_for_messaging_backends(self, validated_data):
        templates = validated_data.get("templates", {})

        messaging_backends_templates = self.instance.messaging_backends_templates if self.instance else None

        for backend_id, backend in get_messaging_backends():
            backend_templates = {}
            if messaging_backends_templates is not None:
                backend_templates = messaging_backends_templates.get(backend_id, {})

            for field in backend.template_fields:
                try:
                    template = templates[backend_id.lower()][field]
                except KeyError:
                    continue

                backend_templates[field] = template

            # remove backend-specific template from payload
            templates.pop(backend_id.lower(), None)

            if backend_templates:
                validated_data["messaging_backends_templates"] = messaging_backends_templates or {} | {
                    backend_id: backend_templates
                }

        return validated_data

    @staticmethod
    def _get_messaging_backend_templates(instance):
        result = {}
        messaging_backends_templates = instance.messaging_backends_templates or {}

        for backend_id, backend in get_messaging_backends():
            if not backend.template_fields:
                continue

            result[backend_id.lower()] = {
                field: messaging_backends_templates.get(backend_id, {}).get(field) for field in backend.template_fields
            }

        return result

    def get_heartbeat(self, obj):
        try:
            heartbeat = obj.integration_heartbeat
        except ObjectDoesNotExist:
            return None
        return IntegrationHeartBeatSerializer(heartbeat).data

    @timed_lru_cache(timeout=5)
    def _get_default_route_iterative(self, obj):
        """
        Gets default route iterative to not hit db on each integration instance.
        """
        for filter in obj.channel_filters.all():
            if filter.is_default:
                return filter


class IntegrationUpdateSerializer(IntegrationSerializer):
    type = IntegrationTypeField(source="integration", read_only=True)
    team_id = TeamPrimaryKeyRelatedField(source="team", read_only=True)

    def update(self, instance, validated_data):
        validated_data = self._correct_validated_data(validated_data)
        default_route_data = validated_data.pop("default_route", None)
        default_route = instance.default_channel_filter
        if default_route_data:
            serializer = DefaultChannelFilterSerializer(default_route, default_route_data, context=self.context)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return super().update(instance, validated_data)
