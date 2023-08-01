from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from jinja2 import TemplateSyntaxError
from rest_framework import fields, serializers

from apps.alerts.grafana_alerting_sync_manager.grafana_alerting_sync import GrafanaAlertingSyncManager
from apps.alerts.models import AlertReceiveChannel
from apps.base.messaging import get_messaging_backends
from apps.integrations.legacy_prefix import has_legacy_prefix, remove_legacy_prefix
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import PHONE_CALL, SLACK, SMS, TELEGRAM, WEB, EagerLoadingMixin
from common.jinja_templater import jinja_template_env
from common.utils import timed_lru_cache

from .integtration_heartbeat import IntegrationHeartBeatSerializer
from .maintenance import MaintainableObjectSerializerMixin
from .routes import DefaultChannelFilterSerializer

# Behaviour templates are named differently in public api
PUBLIC_BEHAVIOUR_TEMPLATES_FIELDS = ["resolve_signal", "grouping_key", "acknowledge_signal", "source_link"]

# TEMPLATE_PUBLIC_API_NAME_TO_DB_FIELD is map from template name in public api to its db field.
# It's applied only for legacy messengers, which are not using messaging backend system
TEMPLATE_PUBLIC_API_NAME_TO_DB_FIELD = {
    "grouping_key": "grouping_id_template",
    "resolve_signal": "resolve_condition_template",
    "acknowledge_signal": "acknowledge_condition_template",
    "source_link": "source_link_template",
    "slack": {
        "title": "slack_title_template",
        "message": "slack_message_template",
        "image_url": "slack_image_url_template",
    },
    "web": {
        "title": "web_title_template",
        "message": "web_message_template",
        "image_url": "web_image_url_template",
    },
    "sms": {
        "title": "sms_title_template",
    },
    "phone_call": {
        "title": "phone_call_title_template",
    },
    "telegram": {
        "title": "telegram_title_template",
        "message": "telegram_message_template",
        "image_url": "telegram_image_url_template",
    },
}

TEMPLATES_WITH_SEPARATE_DB_FIELD = [SLACK, WEB, PHONE_CALL, SMS, TELEGRAM] + PUBLIC_BEHAVIOUR_TEMPLATES_FIELDS

PUBLIC_API_CUSTOMIZABLE_NOTIFICATION_CHANNEL_TEMPLATES = [SLACK, WEB, PHONE_CALL, SMS, TELEGRAM]
for backend_id, backend in get_messaging_backends():
    if backend.customizable_templates:
        PUBLIC_API_CUSTOMIZABLE_NOTIFICATION_CHANNEL_TEMPLATES.append(backend.slug)


class IntegrationTypeField(fields.CharField):
    def to_representation(self, value):
        return remove_legacy_prefix(value)

    def to_internal_value(self, data):
        if data not in AlertReceiveChannel.INTEGRATION_TYPES:
            raise BadRequest(detail="Invalid integration type")
        if has_legacy_prefix(data):
            raise BadRequest("This integration type is deprecated")
        return data


class IntegrationSerializer(EagerLoadingMixin, serializers.ModelSerializer, MaintainableObjectSerializerMixin):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    name = serializers.CharField(required=False, source="verbal_name")
    team_id = TeamPrimaryKeyRelatedField(required=False, allow_null=True, source="team")
    link = serializers.ReadOnlyField(source="integration_url")
    inbound_email = serializers.ReadOnlyField()
    type = IntegrationTypeField(source="integration")
    templates = serializers.DictField(required=False)
    default_route = serializers.DictField(required=False)
    heartbeat = serializers.SerializerMethodField()
    description_short = serializers.CharField(max_length=250, required=False, allow_null=True)

    PREFETCH_RELATED = ["channel_filters"]
    SELECT_RELATED = ["organization", "integration_heartbeat"]

    class Meta:
        model = AlertReceiveChannel
        fields = MaintainableObjectSerializerMixin.Meta.fields + [
            "id",
            "name",
            "description_short",
            "team_id",
            "link",
            "inbound_email",
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
            # TODO: probably only needs to check if unified alerting is on
            connection_error = GrafanaAlertingSyncManager.check_for_connection_errors(organization)
            if connection_error:
                raise serializers.ValidationError(connection_error)
        with transaction.atomic():
            try:
                instance = AlertReceiveChannel.create(
                    **validated_data,
                    author=self.context["request"].user,
                    organization=organization,
                )
            except AlertReceiveChannel.DuplicateDirectPagingError:
                raise BadRequest(detail=AlertReceiveChannel.DuplicateDirectPagingError.DETAIL)
            if default_route_data:
                serializer = DefaultChannelFilterSerializer(
                    instance.default_channel_filter, default_route_data, context=self.context
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
        return instance

    def update(self, *args, **kwargs):
        try:
            return super().update(*args, **kwargs)
        except AlertReceiveChannel.DuplicateDirectPagingError:
            raise BadRequest(detail=AlertReceiveChannel.DuplicateDirectPagingError.DETAIL)

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

    def validate_templates(self, templates):
        if not isinstance(templates, dict):
            raise BadRequest(detail="Invalid template data")

        for notification_channel in PUBLIC_API_CUSTOMIZABLE_NOTIFICATION_CHANNEL_TEMPLATES:
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

        for template_name in PUBLIC_BEHAVIOUR_TEMPLATES_FIELDS:
            template_data = templates.get(template_name, "")
            if template_data is None:
                continue
            if not isinstance(template_data, str):
                raise BadRequest(detail=f"Invalid {template_name} template data")
            try:
                jinja_template_env.from_string(template_data)
            except TemplateSyntaxError:
                raise BadRequest(detail=f"Invalid {template_name} template data")
        return templates

    def _correct_validated_data(self, validated_data):
        """
        Process input templates data.
        1. Reshapes it.
          1.1 We are receiving templates in dict format
            {
              resolve_signal: "resolve me!"
              slack: {
                title: "title",
                message: "message",
                image_url: "image_url",
              },
              ...
            }
          but store them in separate fields: slack_title_template, slack_message_template.
          See _correct_validated_data_for_legacy_template method

          1.2 We are storing templates from messaging backends in separate messaging_backends_templates field.
          So, we need to shape input data related to messaging_backends_templates also.
        2. Handle None templates.
         Public API set template to default value in two cases: (This behaviour is required by terraform plugin).
         2.1 None for the whole template:
         {
           slack: None,
           ...
         }
         In that case all slack templates will be set to default.

         2.2 One particular field is None:
         {
           slack: {
             title: "My custom title:
             message: None,
           },
           ...
         }
         In that case slack message template will be set to default.

        TODO: System described above is too complicated, should be simplified.
        It can be simplified via unification all chatops integrations and messaging_backends
        and/or by introducing unified templates
        """

        validated_data = self._correct_validated_data_for_messaging_backends_templates(validated_data)

        validated_data = self._correct_validated_data_for_legacy_templates(validated_data)

        validated_data.pop("templates", {})
        return validated_data

    def _correct_validated_data_for_legacy_templates(self, validated_data):
        """
        _correct_validated_data_for_legacy_template reshapes validated data to store them.
        It converts data from "templates" dict to db fields, which were used before messaging backends.
        Example:
            {
              "slack": {
                "title": Hello
              }
            }
            Will be converted to

            slack_title_template=Hello
        """
        templates_data_from_request = validated_data.get("templates", {})
        for template_backend_name, template_from_request in templates_data_from_request.items():
            # correct_validated_data for templates with its own db fields.
            if template_backend_name in TEMPLATES_WITH_SEPARATE_DB_FIELD:
                if type(template_from_request) is str:  # if it's plain template: {"resolve_signal": "resolve me"}
                    try:
                        validated_data[
                            TEMPLATE_PUBLIC_API_NAME_TO_DB_FIELD[template_backend_name]
                        ] = template_from_request
                    except KeyError:
                        raise BadRequest(detail="Invalid template data")
                elif type(template_from_request) is dict:  # if it's nested template: {slack: {"title": "some title"}}
                    for attr, template in template_from_request.items():
                        try:
                            validated_data[TEMPLATE_PUBLIC_API_NAME_TO_DB_FIELD[template_backend_name][attr]] = template
                        except KeyError:
                            raise BadRequest(detail="Invalid template data")
                elif template_from_request is None:
                    # if it's we receive None, it's needed to set template to default value
                    try:
                        template_to_set_to_default = TEMPLATE_PUBLIC_API_NAME_TO_DB_FIELD[template_backend_name]
                        if type(template_to_set_to_default) is str:
                            # if we receive None for plain template just set it to None
                            validated_data[TEMPLATE_PUBLIC_API_NAME_TO_DB_FIELD[template_backend_name]] = None
                        elif type(template_to_set_to_default) is dict:
                            # if we receive None for nested template set all it's fields to None
                            for key in template_to_set_to_default.keys():
                                validated_data[TEMPLATE_PUBLIC_API_NAME_TO_DB_FIELD[template_backend_name][key]] = None
                    except KeyError:
                        raise BadRequest(detail="Invalid template data")

        return validated_data

    def _correct_validated_data_for_messaging_backends_templates(self, validated_data):
        """
        _correct_validated_data_for_messaging_backends_templates reshapes validated data to store them.
        It converts data from "templates" dict to messaging_backends_templates field format.
        Example:
            {
              "msteams": {
                "title": Hello
              }
            }
            Will be converted to

            messaging_backends={"MSTEAMS": {"title": "Hello"},
        """
        templates_data_from_request = validated_data.get("templates", {})

        messaging_backends_templates = self.instance.messaging_backends_templates if self.instance else {}
        if messaging_backends_templates is None:
            messaging_backends_templates = {}

        for backend_id, backend in get_messaging_backends():
            if not backend.customizable_templates:
                continue
            backend_template = {}
            if backend.slug in templates_data_from_request:  # check to modify only templates from request data
                template_from_request = templates_data_from_request[backend.slug]
            else:
                continue
            if template_from_request is None:
                # If we receive None backend template, like {"msteams": None }, set all template fields to none.
                for field in backend.template_fields:
                    backend_template[field] = None
            elif type(template_from_request) is dict:
                # go through existing backend_template and update with values from request
                backend_template = messaging_backends_templates.get(backend_id, {})
                for field in backend.template_fields:
                    try:
                        updated_field_template = template_from_request[field]
                    except KeyError:
                        continue

                    backend_template[field] = updated_field_template

            # remove backend-specific template from payload
            templates_data_from_request.pop(backend.slug, None)

            if backend_template:
                messaging_backends_templates[backend_id] = backend_template

        validated_data["messaging_backends_templates"] = messaging_backends_templates
        return validated_data

    @staticmethod
    def _get_messaging_backend_templates(instance):
        result = {}
        messaging_backends_templates = instance.messaging_backends_templates or {}

        for backend_id, backend in get_messaging_backends():
            if not backend.customizable_templates:
                continue
            if not backend.template_fields:
                continue
            result[backend.slug] = {
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

    def update(self, instance, validated_data):
        validated_data = self._correct_validated_data(validated_data)
        default_route_data = validated_data.pop("default_route", None)
        default_route = instance.default_channel_filter
        if default_route_data:
            serializer = DefaultChannelFilterSerializer(default_route, default_route_data, context=self.context)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return super().update(instance, validated_data)
