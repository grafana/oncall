import json
from dataclasses import asdict

from django.core.exceptions import ObjectDoesNotExist
from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.alerts.models import AlertGroup, AlertReceiveChannel
from apps.api.label_filtering import parse_label_query
from apps.api.permissions import RBACPermission
from apps.api.serializers.webhook import WebhookResponseSerializer, WebhookSerializer
from apps.api.views.labels import schedule_update_label_cache
from apps.auth_token.auth import PluginAuthentication
from apps.labels.utils import is_labels_feature_enabled
from apps.webhooks.models import PersonalNotificationWebhook, Webhook, WebhookResponse
from apps.webhooks.presets.preset_options import WebhookPresetOptions
from apps.webhooks.tasks import execute_webhook
from apps.webhooks.utils import apply_jinja_template_for_json
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.filters import (
    ByTeamModelFieldFilterMixin,
    ModelFieldFilterMixin,
    MultipleChoiceCharFilter,
    TeamModelMultipleChoiceFilter,
)
from common.api_helpers.mixins import PublicPrimaryKeyMixin, TeamFilteringMixin
from common.insight_log import EntityEvent, write_resource_insight_log
from common.jinja_templater.apply_jinja_template import JinjaTemplateError, JinjaTemplateWarning

NEW_WEBHOOK_PK = "new"

RECENT_RESPONSE_LIMIT = 20

WEBHOOK_URL = "url"
WEBHOOK_HEADERS = "headers"
WEBHOOK_TRIGGER_TEMPLATE = "trigger_template"
WEBHOOK_TRIGGER_DATA = "data"

WEBHOOK_TEMPLATE_NAMES = [WEBHOOK_URL, WEBHOOK_HEADERS, WEBHOOK_TRIGGER_TEMPLATE, WEBHOOK_TRIGGER_DATA]


def get_integration_queryset(request):
    if request is None:
        return AlertReceiveChannel.objects.none()

    return AlertReceiveChannel.objects_with_maintenance.filter(organization=request.user.organization)


class WebhooksFilter(ByTeamModelFieldFilterMixin, ModelFieldFilterMixin, filters.FilterSet):
    team = TeamModelMultipleChoiceFilter()
    trigger_type = filters.MultipleChoiceFilter(choices=Webhook.TRIGGER_TYPES)
    integration = MultipleChoiceCharFilter(
        field_name="filtered_integrations",
        queryset=get_integration_queryset,
        to_field_name="public_primary_key",
        method="filter_integration",
    )

    def filter_integration(self, queryset, name, value):
        if not value:
            return queryset
        lookup_kwargs = {f"{name}__in": value}
        # include webhooks without filtered_integrations set (ie. apply to all integrations)
        queryset = queryset.filter(**lookup_kwargs) | queryset.filter(filtered_integrations__isnull=True)
        return queryset


class WebhooksView(TeamFilteringMixin, PublicPrimaryKeyMixin[Webhook], ModelViewSet):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "metadata": [RBACPermission.Permissions.OUTGOING_WEBHOOKS_READ],
        "filters": [RBACPermission.Permissions.OUTGOING_WEBHOOKS_READ],
        "list": [RBACPermission.Permissions.OUTGOING_WEBHOOKS_READ],
        "retrieve": [RBACPermission.Permissions.OUTGOING_WEBHOOKS_READ],
        "create": [RBACPermission.Permissions.OUTGOING_WEBHOOKS_WRITE],
        "update": [RBACPermission.Permissions.OUTGOING_WEBHOOKS_WRITE],
        "partial_update": [RBACPermission.Permissions.OUTGOING_WEBHOOKS_WRITE],
        "destroy": [RBACPermission.Permissions.OUTGOING_WEBHOOKS_WRITE],
        "responses": [RBACPermission.Permissions.OUTGOING_WEBHOOKS_READ],
        "preview_template": [RBACPermission.Permissions.OUTGOING_WEBHOOKS_WRITE],
        "preset_options": [RBACPermission.Permissions.OUTGOING_WEBHOOKS_READ],
        "trigger_manual": [RBACPermission.Permissions.OUTGOING_WEBHOOKS_READ],
        "current_personal_notification": [RBACPermission.Permissions.USER_SETTINGS_READ],
        "set_personal_notification": [RBACPermission.Permissions.USER_SETTINGS_WRITE],
    }

    model = Webhook
    serializer_class = WebhookSerializer

    filter_backends = [SearchFilter, filters.DjangoFilterBackend]
    search_fields = ["public_primary_key", "name"]
    filterset_class = WebhooksFilter

    def perform_create(self, serializer):
        serializer.save()
        write_resource_insight_log(instance=serializer.instance, author=self.request.user, event=EntityEvent.CREATED)

    def perform_update(self, serializer):
        prev_state = serializer.instance.insight_logs_serialized
        serializer.save()
        new_state = serializer.instance.insight_logs_serialized
        write_resource_insight_log(
            instance=serializer.instance,
            author=self.request.user,
            event=EntityEvent.UPDATED,
            prev_state=prev_state,
            new_state=new_state,
        )

    def perform_destroy(self, instance):
        write_resource_insight_log(
            instance=instance,
            author=self.request.user,
            event=EntityEvent.DELETED,
        )
        instance.delete()

    def get_queryset(self, ignore_filtering_by_available_teams=False):
        queryset = Webhook.objects.filter(organization=self.request.auth.organization)
        if self.action == "list":
            # exclude connected integration webhooks when listing entries
            queryset = queryset.filter(is_from_connected_integration=False)

        if not ignore_filtering_by_available_teams:
            queryset = queryset.filter(*self.available_teams_lookup_args).distinct()

        # filter by labels
        label_query = self.request.query_params.getlist("label", [])
        kv_pairs = parse_label_query(label_query)
        for key, value in kv_pairs:
            queryset = queryset.filter(
                labels__key_id=key,
                labels__value_id=value,
            )
        # distinct to remove duplicates after webhooks X labels join
        queryset = queryset.distinct()
        # schedule update of labels cache
        ids = [d.id for d in queryset]
        schedule_update_label_cache(self.model.__name__, self.request.auth.organization, ids)

        return queryset

    def get_object(self):
        # get the object from the whole organization if there is a flag `get_from_organization=true`
        # otherwise get the object from the current team
        get_from_organization = self.request.query_params.get("from_organization", "false") == "true"
        if get_from_organization:
            return self.get_object_from_organization()
        return super().get_object()

    def get_object_from_organization(self):
        # use this method to get the object from the whole organization instead of the current team
        pk = self.kwargs["pk"]
        organization = self.request.auth.organization
        try:
            obj = organization.webhooks.filter(*self.available_teams_lookup_args).distinct().get(public_primary_key=pk)
        except ObjectDoesNotExist:
            raise NotFound

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    @extend_schema(
        responses=inline_serializer(
            name="WebhookFilters",
            fields={
                "name": serializers.CharField(),
                "display_name": serializers.CharField(required=False),
                "type": serializers.CharField(),
                "href": serializers.CharField(),
                "global": serializers.BooleanField(required=False),
            },
            many=True,
        )
    )
    @action(methods=["get"], detail=False)
    def filters(self, request):
        api_root = "/api/internal/v1/"

        filter_options = [
            {"name": "search", "type": "search"},
            {
                "name": "team",
                "type": "team_select",
                "href": api_root + "teams/",
                "global": True,
            },
            {
                "name": "trigger_type",
                "type": "options",
                "options": [{"display_name": label, "value": value} for value, label in Webhook.TRIGGER_TYPES],
            },
            {"name": "integration", "type": "options", "href": api_root + "alert_receive_channels/?filters=true"},
        ]

        if is_labels_feature_enabled(self.request.auth.organization):
            filter_options.append(
                {
                    "name": "label",
                    "display_name": "Label",
                    "type": "labels",
                }
            )

        return Response(filter_options)

    @extend_schema(responses=WebhookResponseSerializer(many=True))
    @action(methods=["get"], detail=True)
    def responses(self, request, pk):
        """Return recent responses data for the webhook."""
        if pk == NEW_WEBHOOK_PK:
            return Response([], status=status.HTTP_200_OK)

        webhook = self.get_object()
        queryset = WebhookResponse.objects.filter(webhook_id=webhook.id, trigger_type=webhook.trigger_type).order_by(
            "-timestamp"
        )[:RECENT_RESPONSE_LIMIT]
        response_serializer = WebhookResponseSerializer(queryset, many=True)
        return Response(response_serializer.data)

    @extend_schema(
        request=inline_serializer(
            name="WebhookPreviewTemplateRequest",
            fields={
                "template_body": serializers.CharField(required=False, allow_null=True),
                "template_name": serializers.CharField(required=False, allow_null=True),
                "payload": serializers.DictField(required=False, allow_null=True),
            },
        ),
        responses=inline_serializer(
            name="WebhookPreviewTemplateResponse",
            fields={
                "preview": serializers.CharField(allow_null=True),
            },
        ),
    )
    @action(methods=["post"], detail=True)
    def preview_template(self, request, pk):
        """Return webhook template preview."""
        if pk != NEW_WEBHOOK_PK:
            self.get_object()  # Check webhook exists

        template_body = request.data.get("template_body", None)
        template_name = request.data.get("template_name", None)
        payload = request.data.get("payload", None)

        if not payload:
            response = {"preview": template_body}
            return Response(response, status=status.HTTP_200_OK)

        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                raise BadRequest(detail={"payload": "Could not parse json"})

        if template_body is None or template_name is None:
            response = {"preview": None}
            return Response(response, status=status.HTTP_200_OK)

        if template_name not in WEBHOOK_TEMPLATE_NAMES:
            raise BadRequest(detail={"template_name": "Unknown template name"})

        try:
            result = apply_jinja_template_for_json(template_body, payload)
        except (JinjaTemplateError, JinjaTemplateWarning) as e:
            return Response({"preview": e.fallback_message}, status.HTTP_200_OK)

        response = {"preview": result}
        return Response(response, status=status.HTTP_200_OK)

    @extend_schema(
        responses={
            status.HTTP_200_OK: inline_serializer(
                name="WebhookPresetOptions",
                fields={
                    "id": serializers.CharField(),
                    "name": serializers.CharField(),
                    "logo": serializers.CharField(),
                    "description": serializers.CharField(),
                    "controlled_fields": serializers.ListField(child=serializers.CharField()),
                },
            )
        },
    )
    @action(methods=["get"], detail=False)
    def preset_options(self, request):
        """Return available webhook preset options."""
        result = [asdict(preset) for preset in WebhookPresetOptions.WEBHOOK_PRESET_CHOICES]
        return Response(result)

    @extend_schema(
        request=inline_serializer(
            name="WebhookTriggerManual",
            fields={
                "alert_group": serializers.CharField(),
            },
        ),
        responses={status.HTTP_200_OK: None},
    )
    @action(methods=["post"], detail=True)
    def trigger_manual(self, request, pk):
        """Trigger specified webhook in the context of the given alert group."""
        user = self.request.user
        organization = self.request.auth.organization
        webhook = self.get_object()
        if webhook.trigger_type != Webhook.TRIGGER_MANUAL:
            raise BadRequest(detail={"trigger_type": "This webhook is not manually triggerable."})

        alert_group_ppk = request.data.get("alert_group")
        if not alert_group_ppk:
            raise BadRequest(detail={"alert_group": "This field is required."})

        alert_groups = AlertGroup.objects.filter(
            channel__organization=organization,
            public_primary_key=alert_group_ppk,
        )
        # check for filtered integrations
        if webhook.filtered_integrations.exists():
            alert_groups = alert_groups.filter(channel_id__in=webhook.filtered_integrations.all())
        try:
            alert_group = alert_groups.get()
        except ObjectDoesNotExist:
            raise NotFound

        execute_webhook.apply_async(
            (webhook.pk, alert_group.pk, user.pk, None), kwargs={"trigger_type": Webhook.TRIGGER_MANUAL}
        )
        return Response(status=status.HTTP_200_OK)

    @extend_schema(
        responses={
            status.HTTP_200_OK: inline_serializer(
                name="PersonalNotificationWebhook",
                fields={
                    "webhook": serializers.CharField(),
                    "context": serializers.DictField(required=False, allow_null=True),
                },
            )
        },
    )
    @action(methods=["get"], detail=False)
    def current_personal_notification(self, request):
        user = self.request.user
        notification_channel = {
            "webhook": None,
            "context": None,
        }
        try:
            personal_webhook = PersonalNotificationWebhook.objects.get(user=user)
        except PersonalNotificationWebhook.DoesNotExist:
            personal_webhook = None

        if personal_webhook is not None:
            notification_channel["webhook"] = personal_webhook.webhook.public_primary_key
            notification_channel["context"] = personal_webhook.context_data

        return Response(notification_channel)

    @extend_schema(
        request=inline_serializer(
            name="PersonalNotificationWebhookRequest",
            fields={
                "webhook": serializers.CharField(),
                "context": serializers.DictField(required=False, allow_null=True),
            },
        ),
        responses={status.HTTP_200_OK: None},
    )
    @action(methods=["post"], detail=False)
    def set_personal_notification(self, request):
        """Set up a webhook as personal notification channel for the user."""
        user = self.request.user

        webhook_id = request.data.get("webhook")
        if not webhook_id:
            raise BadRequest(detail={"webhook": "This field is required."})

        try:
            webhook = Webhook.objects.get(
                organization=user.organization,
                public_primary_key=webhook_id,
                trigger_type=Webhook.TRIGGER_PERSONAL_NOTIFICATION,
            )
        except Webhook.DoesNotExist:
            raise BadRequest(detail={"webhook": "Webhook not found."})

        context = request.data.get("context", None)
        if context is not None:
            if not isinstance(context, dict):
                raise BadRequest(detail={"context": "Invalid context."})

            try:
                context = json.dumps(context)
            except TypeError:
                raise BadRequest(detail={"context": "Invalid context."})

        # set or update personal webhook for user
        PersonalNotificationWebhook.objects.update_or_create(
            user=user,
            defaults={
                "webhook": webhook,
                "additional_context_data": context,
            },
        )
        return Response(status=status.HTTP_200_OK)
