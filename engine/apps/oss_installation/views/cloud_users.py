from collections import OrderedDict

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import IsOwnerOrHasRBACPermissions, RBACPermission
from apps.auth_token.auth import PluginAuthentication
from apps.oss_installation.models import CloudConnector, CloudUserIdentity
from apps.oss_installation.serializers import CloudUserSerializer
from apps.oss_installation.utils import cloud_user_identity_status
from apps.user_management.models import User
from common.api_helpers.mixins import PublicPrimaryKeyMixin
from common.api_helpers.paginators import HundredPageSizePaginator

PERMISSIONS = [RBACPermission.Permissions.OTHER_SETTINGS_WRITE]


class CloudUsersView(HundredPageSizePaginator, APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "get": PERMISSIONS,
        "post": PERMISSIONS,
    }

    def get(self, request):
        organization = request.user.organization

        queryset = User.objects.filter(
            organization=organization,
            **User.build_permissions_query(RBACPermission.Permissions.NOTIFICATIONS_READ, organization),
        )

        if request.user.current_team is not None:
            queryset = queryset.filter(teams=request.user.current_team).distinct()
        emails = list(queryset.values_list("email", flat=True))

        results = self.paginate_queryset(queryset, request, view=self)

        cloud_identities = list(CloudUserIdentity.objects.filter(email__in=emails))
        cloud_identities = {cloud_identity.email: cloud_identity for cloud_identity in cloud_identities}

        response = []

        connector = CloudConnector.objects.first()

        for user in results:
            cloud_identity = cloud_identities.get(user.email, None)
            status, link = cloud_user_identity_status(connector, cloud_identity)
            response.append(
                {
                    "id": user.public_primary_key,
                    "email": user.email,
                    "username": user.username,
                    "cloud_data": {"status": status, "link": link},
                }
            )

        return self.get_paginated_response_with_matched_users_count(response, len(cloud_identities))

    def get_paginated_response_with_matched_users_count(self, data, matched_users_count):
        return Response(
            OrderedDict(
                [
                    ("count", self.page.paginator.count),
                    ("matched_users_count", matched_users_count),
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("results", data),
                ]
            )
        )

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
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "retrieve": PERMISSIONS,
        "sync": PERMISSIONS,
    }

    IsOwnerOrHasUserSettingsAdminPermission = IsOwnerOrHasRBACPermissions(
        [RBACPermission.Permissions.USER_SETTINGS_ADMIN]
    )

    rbac_object_permissions = {
        IsOwnerOrHasUserSettingsAdminPermission: [
            "retrieve",
            "sync",
        ],
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
