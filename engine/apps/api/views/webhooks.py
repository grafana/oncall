import json
from dataclasses import asdict

from django.core.exceptions import ObjectDoesNotExist
from django_filters import rest_framework as filters
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.api.label_filtering import parse_label_query
from apps.api.permissions import RBACPermission
from apps.api.serializers.webhook import WebhookResponseSerializer, WebhookSerializer
from apps.api.views.labels import schedule_update_label_cache
from apps.auth_token.auth import PluginAuthentication
from apps.labels.utils import is_labels_feature_enabled
from apps.webhooks.models import Webhook, WebhookResponse
from apps.webhooks.presets.preset_options import WebhookPresetOptions
from apps.webhooks.utils import apply_jinja_template_for_json
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.filters import ByTeamModelFieldFilterMixin, ModelFieldFilterMixin, TeamModelMultipleChoiceFilter
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


class WebhooksFilter(ByTeamModelFieldFilterMixin, ModelFieldFilterMixin, filters.FilterSet):
    team = TeamModelMultipleChoiceFilter()


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

    @action(methods=["get"], detail=False)
    def filters(self, request):
        filter_name = request.query_params.get("search", None)
        api_root = "/api/internal/v1/"

        filter_options = [
            {
                "name": "team",
                "type": "team_select",
                "href": api_root + "teams/",
                "global": True,
            },
        ]

        if is_labels_feature_enabled(self.request.auth.organization):
            filter_options.append(
                {
                    "name": "label",
                    "display_name": "Label",
                    "type": "labels",
                }
            )

        if filter_name is not None:
            filter_options = list(filter(lambda f: filter_name in f["name"], filter_options))

        return Response(filter_options)

    @action(methods=["get"], detail=True)
    def responses(self, request, pk):
        if pk == NEW_WEBHOOK_PK:
            return Response([], status=status.HTTP_200_OK)

        webhook = self.get_object()
        queryset = WebhookResponse.objects.filter(webhook_id=webhook.id, trigger_type=webhook.trigger_type).order_by(
            "-timestamp"
        )[:RECENT_RESPONSE_LIMIT]
        response_serializer = WebhookResponseSerializer(queryset, many=True)
        return Response(response_serializer.data)

    @action(methods=["post"], detail=True)
    def preview_template(self, request, pk):
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

    @action(methods=["get"], detail=False)
    def preset_options(self, request):
        result = [asdict(preset) for preset in WebhookPresetOptions.WEBHOOK_PRESET_CHOICES]
        return Response(result)
