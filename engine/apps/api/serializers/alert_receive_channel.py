import typing
from collections import OrderedDict

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from drf_spectacular.utils import PolymorphicProxySerializer, extend_schema_field
from jinja2 import TemplateSyntaxError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField, set_value

from apps.alerts.grafana_alerting_sync_manager.grafana_alerting_sync import GrafanaAlertingSyncManager
from apps.alerts.models import AlertReceiveChannel
from apps.alerts.models.channel_filter import ChannelFilter
from apps.base.messaging import get_messaging_backends
from apps.integrations.legacy_prefix import has_legacy_prefix
from apps.labels.models import LabelKeyCache, LabelValueCache
from apps.labels.types import LabelKey
from apps.user_management.models import Organization
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import APPEARANCE_TEMPLATE_NAMES, EagerLoadingMixin
from common.jinja_templater import jinja_template_env

from .integration_heartbeat import IntegrationHeartBeatSerializer
from .labels import LabelsSerializerMixin


def _additional_settings_serializer_from_type(integration_type: str) -> serializers.Serializer:
    """Return serializer class for given integration_type additional settings."""
    cls = None
    config = AlertReceiveChannel.get_config_from_type(integration_type)
    cls = getattr(config, "additional_settings_serializer", None) if config else None
    return cls


# AlertGroupCustomLabelValue represents custom alert group label value for API requests
# It handles two types of label's value:
# 1. Just Label Value from a label repo for a static label
# 2. Templated Label value which is actually a jinja template for a dynamic label.
class AlertGroupCustomLabelValueAPI(typing.TypedDict):
    id: str | None  # None for templated labels, label value ID for plain labels
    name: str  # Jinja template for templated labels, label value name for plain labels
    prescribed: bool  # Indicates of selected label value is prescribed. Not applicable for templated values.


# AlertGroupCustomLabel represents Alert group custom label for API requests
# Key is just a LabelKey from label repo, while value could be value from repo or a jinja template.
class AlertGroupCustomLabelAPI(typing.TypedDict):
    key: LabelKey
    value: AlertGroupCustomLabelValueAPI


AlertGroupCustomLabelsAPI = list[AlertGroupCustomLabelAPI]


class IntegrationAlertGroupLabels(typing.TypedDict):
    inheritable: dict[str, bool]
    custom: AlertGroupCustomLabelsAPI
    template: str | None


AlertReceiveChannelAdditionalSettingsSerializers = (
    i.additional_settings_serializer
    for i in AlertReceiveChannel._config
    if getattr(i, "additional_settings_serializer", None)
)


@extend_schema_field(
    PolymorphicProxySerializer(
        component_name="AdditionalSettingsField",
        serializers=list(AlertReceiveChannelAdditionalSettingsSerializers),
        resource_type_field_name=None,
    )
)
class AdditionalSettingsField(serializers.DictField):
    pass


class CustomLabelSerializer(serializers.Serializer):
    """This serializer is consistent with apps.api.serializers.labels.LabelPairSerializer, but allows null for value ID."""

    class CustomLabelKeySerializer(serializers.Serializer):
        id = serializers.CharField()
        name = serializers.CharField()
        prescribed = serializers.BooleanField(default=False)

    class CustomLabelValueSerializer(serializers.Serializer):
        # ID is null for templated labels. For such labels, the "name" value is a Jinja2 template.
        id = serializers.CharField(allow_null=True)
        name = serializers.CharField()
        prescribed = serializers.BooleanField(default=False)

    key = CustomLabelKeySerializer()
    value = CustomLabelValueSerializer()


class IntegrationAlertGroupLabelsSerializer(serializers.Serializer):
    """Alert group labels configuration for the integration. See AlertReceiveChannel.alert_group_labels for details."""

    inheritable = serializers.DictField(child=serializers.BooleanField())
    custom = CustomLabelSerializer(many=True)
    template = serializers.CharField(allow_null=True)

    @staticmethod
    def pop_alert_group_labels(validated_data: dict) -> IntegrationAlertGroupLabels | None:
        """Get alert group labels from validated data."""

        # the "alert_group_labels" field is optional, so either all 3 fields are present or none
        if "inheritable" not in validated_data:
            return None

        return {
            "inheritable": validated_data.pop("inheritable"),
            "custom": validated_data.pop("custom"),
            "template": validated_data.pop("template"),
        }

    @classmethod
    def update(
        cls, instance: AlertReceiveChannel, alert_group_labels: IntegrationAlertGroupLabels | None
    ) -> AlertReceiveChannel:
        if alert_group_labels is None:
            return instance

        # update inheritable labels
        inheritable_key_ids = [
            key_id for key_id, inheritable in alert_group_labels["inheritable"].items() if inheritable
        ]
        instance.labels.filter(key_id__in=inheritable_key_ids).update(inheritable=True)
        instance.labels.filter(~Q(key_id__in=inheritable_key_ids)).update(inheritable=False)

        # update DB cache for custom labels
        cls._create_custom_labels(instance.organization, alert_group_labels["custom"])
        # update custom labels
        instance.alert_group_labels_custom = cls._custom_labels_to_internal_value(alert_group_labels["custom"])

        # update template
        instance.alert_group_labels_template = alert_group_labels["template"]

        instance.save(update_fields=["alert_group_labels_custom", "alert_group_labels_template"])
        return instance

    @staticmethod
    def _create_custom_labels(organization: Organization, labels: AlertGroupCustomLabelsAPI) -> None:
        """Create LabelKeyCache and LabelValueCache objects for custom labels."""

        label_keys = [
            LabelKeyCache(
                id=label["key"]["id"],
                name=label["key"]["name"],
                prescribed=label["key"]["prescribed"],
                organization=organization,
            )
            for label in labels
        ]

        label_values = [
            LabelValueCache(
                id=label["value"]["id"],
                name=label["value"]["name"],
                prescribed=label["value"]["prescribed"],
                key_id=label["key"]["id"],
            )
            for label in labels
            if label["value"]["id"]  # don't create LabelValueCache objects for templated labels
        ]

        LabelKeyCache.objects.bulk_create(label_keys, ignore_conflicts=True, batch_size=5000)
        LabelValueCache.objects.bulk_create(label_values, ignore_conflicts=True, batch_size=5000)

    @classmethod
    def to_representation(cls, instance: AlertReceiveChannel) -> IntegrationAlertGroupLabels:
        """
        The API representation of alert group labels is very different from the underlying model.

        "inheritable" is based on AlertReceiveChannelAssociatedLabel.inheritable, a property of another model.
        "custom" is based on AlertReceiveChannel.alert_group_labels_custom, a JSONField with a different schema.
        "template" is based on AlertReceiveChannel.alert_group_labels_template, this one is straightforward.
        """

        return {
            "inheritable": {label.key_id: label.inheritable for label in instance.labels.all()},
            "custom": cls._custom_labels_to_representation(instance.alert_group_labels_custom),
            "template": instance.alert_group_labels_template,
        }

    @staticmethod
    def _custom_labels_to_internal_value(
        custom_labels: AlertGroupCustomLabelsAPI,
    ) -> AlertReceiveChannel.AlertGroupCustomLabelsDB:
        """Convert custom labels from API representation to the schema used by the JSONField on the model."""

        return [
            [label["key"]["id"], label["value"]["id"], None if label["value"]["id"] else label["value"]["name"]]
            for label in custom_labels
        ]

    @staticmethod
    def _custom_labels_to_representation(
        custom_labels: AlertReceiveChannel.AlertGroupCustomLabelsDB,
    ) -> AlertGroupCustomLabelsAPI:
        """
        Inverse of the _custom_labels_to_internal_value method above.
        Fetches label names from DB cache, so the API response schema is consistent with other label endpoints.
        """

        from apps.labels.models import LabelKeyCache, LabelValueCache

        if custom_labels is None:
            return []

        # build index of keys id to name and prescribed flag
        label_key_index = {
            k.id: {"name": k.name, "prescribed": k.prescribed}
            for k in LabelKeyCache.objects.filter(id__in=[label[0] for label in custom_labels]).only(
                "id", "name", "prescribed"
            )
        }

        # build index of values id to name and prescribed flag
        label_value_index = {
            v.id: {"name": v.name, "prescribed": v.prescribed}
            for v in LabelValueCache.objects.filter(id__in=[label[1] for label in custom_labels if label[1]]).only(
                "id", "name", "prescribed"
            )
        }

        return [
            {
                "key": {
                    "id": key_id,
                    "name": label_key_index[key_id]["name"],
                    "prescribed": label_key_index[key_id]["prescribed"],
                },
                "value": {
                    "id": value_id if value_id else None,
                    "name": label_value_index[value_id]["name"] if value_id else typing.cast(str, template),
                    "prescribed": label_value_index[value_id]["prescribed"] if value_id else False,
                },
            }
            for key_id, value_id, template in custom_labels
            if key_id in label_key_index and (value_id in label_value_index or not value_id)
        ]


class AlertReceiveChannelSerializer(
    EagerLoadingMixin, LabelsSerializerMixin, serializers.ModelSerializer[AlertReceiveChannel]
):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    integration_url = serializers.ReadOnlyField()
    alert_count = serializers.SerializerMethodField()
    alert_groups_count = serializers.SerializerMethodField()
    author = serializers.CharField(read_only=True, source="author.public_primary_key")
    organization = serializers.CharField(read_only=True, source="organization.public_primary_key")
    team = TeamPrimaryKeyRelatedField(allow_null=True, required=False)
    is_able_to_autoresolve = serializers.ReadOnlyField()
    default_channel_filter = serializers.SerializerMethodField()
    instructions = serializers.SerializerMethodField()
    demo_alert_enabled = serializers.BooleanField(source="is_demo_alert_enabled", read_only=True)
    is_based_on_alertmanager = serializers.BooleanField(source="based_on_alertmanager", read_only=True)
    maintenance_till = serializers.ReadOnlyField(source="till_maintenance_timestamp")
    heartbeat = IntegrationHeartBeatSerializer(read_only=True, allow_null=True, source="integration_heartbeat")
    allow_delete = serializers.SerializerMethodField()
    description_short = serializers.CharField(max_length=250, required=False, allow_null=True)
    demo_alert_payload = serializers.JSONField(source="config.example_payload", read_only=True)
    routes_count = serializers.SerializerMethodField()
    connected_escalations_chains_count = serializers.SerializerMethodField()
    inbound_email = serializers.CharField(required=False, read_only=True)
    is_legacy = serializers.SerializerMethodField()
    alert_group_labels = IntegrationAlertGroupLabelsSerializer(source="*", required=False)
    additional_settings = AdditionalSettingsField(allow_null=True, allow_empty=False, required=False, default=None)

    # integration heartbeat is in PREFETCH_RELATED not by mistake.
    # With using of select_related ORM builds strange join
    # which leads to incorrect heartbeat-alert_receive_channel binding in result
    PREFETCH_RELATED = ["channel_filters", "integration_heartbeat", "labels", "labels__key", "labels__value"]
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
            "routes_count",
            "connected_escalations_chains_count",
            "is_based_on_alertmanager",
            "inbound_email",
            "is_legacy",
            "labels",
            "alert_group_labels",
            "alertmanager_v2_migrated_at",
            "additional_settings",
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
            "routes_count",
            "connected_escalations_chains_count",
            "is_based_on_alertmanager",
            "inbound_email",
            "is_legacy",
            "alertmanager_v2_migrated_at",
        ]
        extra_kwargs = {"integration": {"required": True}}

    def to_internal_value(self, data):
        settings_serializer_cls = (
            _additional_settings_serializer_from_type(self.instance.config.slug) if self.instance else None
        )
        if settings_serializer_cls:
            additional_settings_data = data.get("additional_settings", self.instance.additional_settings)
            settings_serializer = settings_serializer_cls(self.instance, data=additional_settings_data)
            settings_serializer.is_valid()
            if settings_serializer.errors:
                raise ValidationError({"additional_settings": settings_serializer.errors})
            data["additional_settings"] = settings_serializer.to_internal_value(additional_settings_data)
        return super().to_internal_value(data)

    def to_representation(self, instance):
        result = super().to_representation(instance)
        if instance.additional_settings:
            settings_serializer_cls = _additional_settings_serializer_from_type(instance.config.slug)
            if settings_serializer_cls:
                settings_serializer = settings_serializer_cls(instance)
                result["additional_settings"] = settings_serializer.to_representation(instance)
        return result

    def validate(self, data):
        validated_data = super().validate(data)
        self.validate_name_uniqueness(validated_data)
        return validated_data

    def validate_name_uniqueness(self, validated_data):
        organization = self.context["request"].auth.organization
        verbal_name = validated_data.get("verbal_name")
        team = validated_data.get("team", self.instance.team) if self.instance else validated_data.get("team")
        try:
            obj = AlertReceiveChannel.objects.get(organization=organization, team=team, verbal_name=verbal_name)
        except AlertReceiveChannel.DoesNotExist:
            pass
        except AlertReceiveChannel.MultipleObjectsReturned:
            raise serializers.ValidationError(
                {"verbal_name": "An integration with this name already exists for this team"}
            )
        else:
            if self.instance is None or obj.id != self.instance.id:
                raise serializers.ValidationError(
                    {"verbal_name": "An integration with this name already exists for this team"}
                )

    def create(self, validated_data):
        organization = self.context["request"].auth.organization
        integration = validated_data.get("integration")
        create_default_webhooks = validated_data.pop("create_default_webhooks", True)
        if has_legacy_prefix(integration):
            raise BadRequest(detail="This integration is deprecated")
        if integration == AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING:
            connection_error = GrafanaAlertingSyncManager.check_for_connection_errors(organization)
            if connection_error:
                raise BadRequest(detail=connection_error)
        for _integration in AlertReceiveChannel._config:
            if _integration.slug == integration:
                is_able_to_autoresolve = _integration.is_able_to_autoresolve

        # pop associated labels and alert group labels, so they are not passed to AlertReceiveChannel.create
        labels = validated_data.pop("labels", None)
        alert_group_labels = IntegrationAlertGroupLabelsSerializer.pop_alert_group_labels(validated_data)

        try:
            instance = AlertReceiveChannel.create(
                **validated_data,
                organization=organization,
                author=self.context["request"].user,
                allow_source_based_resolving=is_able_to_autoresolve,
            )
        except AlertReceiveChannel.DuplicateDirectPagingError:
            raise BadRequest(detail=AlertReceiveChannel.DuplicateDirectPagingError.DETAIL)

        # Create label associations first, then update alert group labels
        self.update_labels_association_if_needed(labels, instance, organization)
        instance = IntegrationAlertGroupLabelsSerializer.update(instance, alert_group_labels)

        # Create default webhooks if needed
        if create_default_webhooks and hasattr(instance.config, "create_default_webhooks"):
            instance.config.create_default_webhooks(instance)

        return instance

    def update(self, instance, validated_data):
        # update associated labels
        labels = validated_data.pop("labels", None)
        self.update_labels_association_if_needed(labels, instance, self.context["request"].auth.organization)

        # update alert group labels
        instance = IntegrationAlertGroupLabelsSerializer.update(
            instance, IntegrationAlertGroupLabelsSerializer.pop_alert_group_labels(validated_data)
        )

        try:
            updated_instance = super().update(instance, validated_data)
        except AlertReceiveChannel.DuplicateDirectPagingError:
            raise BadRequest(detail=AlertReceiveChannel.DuplicateDirectPagingError.DETAIL)

        # update webhooks if needed, using updated instance
        if hasattr(instance.config, "update_default_webhooks"):
            instance.config.update_default_webhooks(updated_instance)

        return updated_instance

    def get_instructions(self, obj: "AlertReceiveChannel") -> str:
        # Deprecated, kept for api-backward compatibility
        return ""

    # MethodFields are used instead of relevant properties because of properties hit db on each instance in queryset
    def get_default_channel_filter(self, obj: "AlertReceiveChannel") -> str | None:
        for filter in obj.channel_filters.all():
            if filter.is_default:
                return filter.public_primary_key
        return None

    @staticmethod
    def validate_integration(integration):
        if integration is None or integration not in AlertReceiveChannel.WEB_INTEGRATION_CHOICES:
            raise BadRequest(detail="invalid integration")

        if integration == AlertReceiveChannel.INTEGRATION_DIRECT_PAGING:
            raise BadRequest(detail="Direct paging integrations can't be created")

        return integration

    def validate_additional_settings(self, data):
        integration = self.instance.integration if self.instance else self.initial_data.get("integration")
        settings_serializer_cls = _additional_settings_serializer_from_type(integration)
        if settings_serializer_cls:
            if not data:
                raise ValidationError(["This field is required for this integration."])
            serializer = settings_serializer_cls(data=data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
        elif data is not None:
            raise ValidationError(["Invalid data"])
        return data

    def get_allow_delete(self, obj: "AlertReceiveChannel") -> bool:
        # don't allow deleting direct paging integrations
        return obj.integration != AlertReceiveChannel.INTEGRATION_DIRECT_PAGING

    def get_alert_count(self, obj: "AlertReceiveChannel") -> int:
        return 0

    def get_alert_groups_count(self, obj: "AlertReceiveChannel") -> int:
        return 0

    def get_routes_count(self, obj: "AlertReceiveChannel") -> int:
        return obj.channel_filters.count()

    def get_is_legacy(self, obj: "AlertReceiveChannel") -> bool:
        return has_legacy_prefix(obj.integration)

    def get_connected_escalations_chains_count(self, obj: "AlertReceiveChannel") -> int:
        return (
            ChannelFilter.objects.filter(alert_receive_channel=obj, escalation_chain__isnull=False)
            .values("escalation_chain")
            .distinct()
            .count()
        )


class AlertReceiveChannelCreateSerializer(AlertReceiveChannelSerializer):
    create_default_webhooks = serializers.BooleanField(required=False, default=True)

    class Meta(AlertReceiveChannelSerializer.Meta):
        fields = [
            *AlertReceiveChannelSerializer.Meta.fields,
            "create_default_webhooks",
        ]


class AlertReceiveChannelUpdateSerializer(AlertReceiveChannelSerializer):
    class Meta(AlertReceiveChannelSerializer.Meta):
        read_only_fields = [*AlertReceiveChannelSerializer.Meta.read_only_fields, "integration"]


class FastAlertReceiveChannelSerializer(serializers.ModelSerializer[AlertReceiveChannel]):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    integration = serializers.CharField(read_only=True)
    deleted = serializers.SerializerMethodField()

    class Meta:
        model = AlertReceiveChannel
        fields = ["id", "integration", "verbal_name", "deleted"]

    def get_deleted(self, obj: "AlertReceiveChannel") -> bool:
        return obj.deleted_at is not None


class FilterAlertReceiveChannelSerializer(serializers.ModelSerializer[AlertReceiveChannel]):
    # don't use get_value as the method name, otherwise this will override the get_value method on
    # serializers.ModelSerializer, which may cause unexpected behavior (+ this violates the "Lisov substition
    # principle" which mypy complains about)
    value = serializers.SerializerMethodField(method_name="_get_value")
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = AlertReceiveChannel
        fields = ["value", "display_name", "integration_url"]

    def _get_value(self, obj: "AlertReceiveChannel") -> str:
        return obj.public_primary_key

    def get_display_name(self, obj: "AlertReceiveChannel") -> str:
        display_name = obj.verbal_name or AlertReceiveChannel.INTEGRATION_CHOICES[obj.integration][1]
        return display_name


class AlertReceiveChannelTemplatesSerializer(EagerLoadingMixin, serializers.ModelSerializer[AlertReceiveChannel]):
    id = serializers.CharField(read_only=True, source="public_primary_key")

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

    def get_payload_example(self, obj: "AlertReceiveChannel"):
        from apps.alerts.models import AlertGroup

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

    def get_is_based_on_alertmanager(self, obj: "AlertReceiveChannel"):
        return obj.based_on_alertmanager

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

        for field_name in self.core_templates_names:
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

    def to_representation(self, obj: "AlertReceiveChannel"):
        ret = super().to_representation(obj)

        core_templates = self._get_core_templates(obj)
        ret.update(core_templates)

        # include messaging backend templates
        additional_templates = self._get_messaging_backend_templates(obj)
        ret.update(additional_templates)

        return ret

    def _get_messaging_backend_templates(self, obj: "AlertReceiveChannel"):
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
                if not value and not backend.skip_default_template_fields:
                    value = obj.get_default_template_attribute(backend_id, field)
                    is_default = True
                field_name = f"{backend.slug}_{field}_template"
                templates[field_name] = value
                templates[f"{field_name}_is_default"] = is_default
        return templates

    def _get_core_templates(self, obj: "AlertReceiveChannel"):
        core_templates = {}

        for template_name in self.core_templates_names:
            template_value = getattr(obj, template_name)
            defaults = getattr(obj, f"INTEGRATION_TO_DEFAULT_{template_name.upper()}", {})
            default_template_value = defaults.get(obj.integration)
            core_templates[template_name] = template_value or default_template_value
            core_templates[f"{template_name}_is_default"] = not bool(template_value)

        return core_templates

    @property
    def core_templates_names(self) -> typing.List[str]:
        """
        returns names of templates introduced before messaging backends system with respect to enabled integrations.
        """
        core_templates = [
            "web_title_template",
            "web_message_template",
            "web_image_url_template",
            "sms_title_template",
            "phone_call_title_template",
            "source_link_template",
            "grouping_id_template",
            "resolve_condition_template",
            "acknowledge_condition_template",
        ]

        if settings.FEATURE_SLACK_INTEGRATION_ENABLED:
            core_templates += [
                "slack_title_template",
                "slack_message_template",
                "slack_image_url_template",
            ]
        if settings.FEATURE_TELEGRAM_INTEGRATION_ENABLED:
            core_templates += [
                "telegram_title_template",
                "telegram_message_template",
                "telegram_image_url_template",
            ]
        return core_templates
