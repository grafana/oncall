from rest_framework import status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.api.permissions import IsStaff
from apps.api.serializers.organization import PluginOrganizationSerializer
from apps.grafana_plugin.helpers.client import GrafanaAPIClient
from apps.user_management.models import Organization
from apps.user_management.sync import sync_organization
from common.api_helpers.mixins import PublicPrimaryKeyMixin


class PluginInstallationsView(
    PublicPrimaryKeyMixin,
    CreateModelMixin,
    RetrieveModelMixin,
    ListModelMixin,
    GenericViewSet,
):
    authentication_classes = [BasicAuthentication, SessionAuthentication]
    permission_classes = (IsStaff,)

    model = Organization
    serializer_class = PluginOrganizationSerializer

    def get_queryset(self):
        return Organization.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization = serializer.save()
        sync_organization(organization)
        return Response(data=organization.provision_plugin(), status=status.HTTP_201_CREATED)

    @action(methods=["post"], detail=True)
    def revoke_and_reissue(self, request, pk):
        organization = self.get_object()
        serializer = self.get_serializer(organization, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=organization.provision_plugin())

    @action(methods=["post"], detail=True)
    def revoke(self, request, pk):
        organization = self.get_object()
        organization.revoke_plugin()
        return Response(data={"details": "Plugin token revoked"})

    @action(methods=["get"], detail=True)
    def status(self, request, pk):
        organization = self.get_object()
        client = GrafanaAPIClient(api_url=organization.grafana_url, api_token=organization.api_token)
        _, grafana_status = client.check_token()
        return Response(data=grafana_status)

    @action(methods=["post"], detail=True)
    def sync_organization(self, request, pk):
        organization = self.get_object()
        sync_organization(organization)
        return Response(data={"details": "Sync organization complete"})
