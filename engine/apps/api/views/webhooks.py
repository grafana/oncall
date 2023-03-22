from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.api.permissions import RBACPermission
from apps.api.serializers.webhook import WebhookSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.webhooks.models import Webhook
from common.api_helpers.mixins import PublicPrimaryKeyMixin, TeamFilteringMixin


class WebhooksView(TeamFilteringMixin, PublicPrimaryKeyMixin, ModelViewSet):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "metadata": [RBACPermission.Permissions.OUTGOING_WEBHOOKS_READ],
        "list": [RBACPermission.Permissions.OUTGOING_WEBHOOKS_READ],
        "retrieve": [RBACPermission.Permissions.OUTGOING_WEBHOOKS_READ],
        "create": [RBACPermission.Permissions.OUTGOING_WEBHOOKS_WRITE],
        "update": [RBACPermission.Permissions.OUTGOING_WEBHOOKS_WRITE],
        "partial_update": [RBACPermission.Permissions.OUTGOING_WEBHOOKS_WRITE],
        "destroy": [RBACPermission.Permissions.OUTGOING_WEBHOOKS_WRITE],
    }

    model = Webhook
    serializer_class = WebhookSerializer

    def get_queryset(self, ignore_filtering_by_available_teams=False):
        queryset = Webhook.objects.filter(
            organization=self.request.auth.organization,
        ).prefetch_related("responses")
        if not ignore_filtering_by_available_teams:
            queryset = queryset.filter(*self.available_teams_lookup_args).distinct()
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
            obj = organization.webhooks.get(public_primary_key=pk)
        except ObjectDoesNotExist:
            raise NotFound

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def perform_create(self, serializer):
        self.check_webhooks_2_enabled()
        serializer.save()

    def perform_update(self, serializer):
        self.check_webhooks_2_enabled()
        serializer.save()

    def perform_destroy(self, instance):
        self.check_webhooks_2_enabled()
        instance.delete()

    def check_webhooks_2_enabled(self):
        DynamicSetting = apps.get_model("base", "DynamicSetting")
        enabled_webhooks_2_orgs = DynamicSetting.objects.get_or_create(
            name="enabled_webhooks_2_orgs",
            defaults={
                "json_value": {
                    "org_ids": [],
                }
            },
        )[0]
        if self.request.auth.organization.pk not in enabled_webhooks_2_orgs.json_value["org_ids"]:
            raise PermissionDenied("Webhooks 2 not enabled for organization. Permission denied.")
