from django.conf import settings
from rest_framework import mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from apps.api.permissions import RBACPermission
from apps.auth_token.auth import ApiTokenAuthentication, GrafanaServiceAccountAuthentication
from apps.public_api.serializers.zoom_channel import ZoomChannelSerializer
from apps.public_api.throttlers.user_throttle import UserThrottle
from common.api_helpers.mixins import RateLimitHeadersMixin
from common.api_helpers.paginators import FiftyPageSizePaginator


class ZoomChannelView(RateLimitHeadersMixin, mixins.ListModelMixin, GenericViewSet):
    authentication_classes = (GrafanaServiceAccountAuthentication, ApiTokenAuthentication)
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "list": [RBACPermission.Permissions.CHATOPS_READ],
    }

    pagination_class = FiftyPageSizePaginator
    throttle_classes = [UserThrottle]

    serializer_class = ZoomChannelSerializer

    def get_queryset(self):
        if not getattr(settings, 'FEATURE_ZOOM_INTEGRATION_ENABLED', False):
            from apps.zoom.models import ZoomChannel
            return ZoomChannel.objects.none()

        from apps.zoom.models import ZoomChannel

        channel_name = self.request.query_params.get("channel_name", None)

        queryset = ZoomChannel.objects.filter(
            organization=self.request.auth.organization,
        ).distinct()

        if channel_name:
            queryset = queryset.filter(channel_name=channel_name)

        return queryset.order_by("id")
