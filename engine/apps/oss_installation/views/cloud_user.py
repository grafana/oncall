from urllib.parse import urljoin

from rest_framework import mixins, serializers, viewsets
from rest_framework.permissions import IsAuthenticated

import apps.oss_installation.constants as cloud_constants
from apps.api.permissions import ActionPermission, IsOwnerOrAdmin
from apps.auth_token.auth import PluginAuthentication
from apps.oss_installation.models import CloudOrganizationConnector, CloudUserIdentity
from apps.user_management.models import User
from common.api_helpers.mixins import PublicPrimaryKeyMixin


class CloudUserSerializer(serializers.ModelSerializer):
    cloud_data = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["sync_data"]

    def get_cloud_data(self, obj):
        link = None
        status = cloud_constants.CLOUD_NOT_SYNCED
        connector = CloudOrganizationConnector.objects.filter(
            organization=self.context["request"].auth.organization
        ).first()
        if connector is not None:
            cloud_user_identity = CloudUserIdentity.objects.filter(email=obj.email).first()
            if cloud_user_identity is None:
                status = cloud_constants.CLOUD_SYNCED_USER_NOT_FOUND
                link = connector.cloud_url
            elif not cloud_user_identity.phone_number_verified:
                status = cloud_constants.CLOUD_SYNCED_USER_NOT_FOUND
                link = urljoin(
                    connector.cloud_url, f"a/grafana-oncall-app/?page=users&p=1&id={cloud_user_identity.cloud_id}"
                )
            else:
                status = cloud_constants.CLOUD_SYNCED_PHONE_VERIFIED
                link = urljoin(
                    connector.cloud_url, f"a/grafana-oncall-app/?page=users&p=1&id={cloud_user_identity.cloud_id}"
                )
        cloud_data = {"status": status, "link": link}
        return cloud_data


class CloudUserView(
    PublicPrimaryKeyMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, ActionPermission)

    action_object_permissions = {
        IsOwnerOrAdmin: ("retrieve",),
    }
    serializer_class = CloudUserSerializer

    def get_queryset(self):
        queryset = User.objects.filter(organization=self.request.user.organization)
        return queryset
