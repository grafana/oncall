from urllib.parse import urljoin

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

import apps.oss_installation.constants as cloud_constants
from apps.api.permissions import ActionPermission, AnyRole, IsAdmin, IsOwnerOrAdmin
from apps.auth_token.auth import PluginAuthentication
from apps.oss_installation.models import CloudConnector, CloudUserIdentity
from apps.oss_installation.serializers import CloudUserSerializer
from apps.user_management.models import User
from common.api_helpers.mixins import PublicPrimaryKeyMixin
from common.api_helpers.paginators import HundredPageSizePaginator


class CloudUsersView(HundredPageSizePaginator, APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, IsAdmin)

    def get(self, request):
        organization = request.user.organization

        queryset = User.objects.filter(organization=organization)

        if request.user.current_team is not None:
            queryset = queryset.filter(teams=request.user.current_team).distinct()

        results = self.paginate_queryset(queryset, request, view=self)

        emails = list(queryset.values_list("email", flat=True))
        cloud_identities = list(CloudUserIdentity.objects.filter(email__in=emails))
        cloud_identities = {cloud_identity.email: cloud_identity for cloud_identity in cloud_identities}

        response = []

        connector = CloudConnector.objects.first()

        for user in results:
            link = None
            status = cloud_constants.CLOUD_NOT_SYNCED
            if connector is not None:
                status = cloud_constants.CLOUD_SYNCED_USER_NOT_FOUND
                cloud_identity = cloud_identities.get(user.email, None)
                if cloud_identity:
                    status = cloud_constants.CLOUD_SYNCED_PHONE_NOT_VERIFIED
                    is_phone_verified = cloud_identity.phone_number_verified
                    if is_phone_verified:
                        status = cloud_constants.CLOUD_SYNCED_PHONE_VERIFIED
                    link = urljoin(
                        connector.cloud_url, f"a/grafana-oncall-app/?page=users&p=1&id={cloud_identity.cloud_id}"
                    )

            response.append(
                {
                    "id": user.public_primary_key,
                    "email": user.email,
                    "username": user.username,
                    "cloud_data": {"status": status, "link": link},
                }
            )

        return self.get_paginated_response(response)

    def post(self, request):
        connector = CloudConnector.objects.first()
        if connector is not None:
            sync_status, err = connector.sync_users_with_cloud()
            return Response(status=status.HTTP_200_OK, data={"status": sync_status, "error": err})
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"detail": "Grafana Cloud is not connected"})


class CloudUserView(
    PublicPrimaryKeyMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, ActionPermission)

    action_permissions = {
        AnyRole: ("retrieve",),
        IsAdmin: ("sync",),
    }
    action_object_permissions = {
        IsOwnerOrAdmin: ("retrieve", "sync"),
    }
    serializer_class = CloudUserSerializer

    def get_queryset(self):
        queryset = User.objects.filter(organization=self.request.user.organization)
        return queryset

    @action(detail=True, methods=["post"])
    def sync(self, request, pk):
        user = self.get_object()
        connector = CloudConnector.objects.first()
        if connector is not None:
            sync_status, err = connector.sync_user_with_cloud(user)
            return Response(status=status.HTTP_200_OK, data={"status": sync_status, "error": err})
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"detail": "Grafana Cloud is not connected"})
