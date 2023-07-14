from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.alerts.models import AlertGroup, AlertReceiveChannel
from apps.api.permissions import RBACPermission
from apps.api.views.common.alert_group import STATS_MAX_COUNT, AlertGroupFilter, AlertGroupFilterBackend
from apps.auth_token.auth import PluginAuthentication
from apps.mobile_app.auth import MobileAppAuthTokenAuthentication


class AlertGroupView(viewsets.GenericViewSet):
    authentication_classes = (MobileAppAuthTokenAuthentication, PluginAuthentication)
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "stats": [RBACPermission.Permissions.ALERT_GROUPS_READ],
    }

    filter_backends = [SearchFilter, AlertGroupFilterBackend]

    filterset_class = AlertGroupFilter

    def get_queryset(self):
        alert_receive_channels_qs = AlertReceiveChannel.objects.filter(
            organization_id=self.request.auth.organization.id
        )

        alert_receive_channels_ids = list(alert_receive_channels_qs.values_list("id", flat=True))

        return AlertGroup.unarchived_objects.filter(channel__in=alert_receive_channels_ids).only("id")

    @action(detail=False)
    def stats(self, *args, **kwargs):
        alert_groups = self.filter_queryset(self.get_queryset())[:STATS_MAX_COUNT]
        count = alert_groups.count()
        count = f"{STATS_MAX_COUNT-1}+" if count == STATS_MAX_COUNT else str(count)
        return Response(
            # TODO: we should figure out a better way than hardcoding these...
            # we likely need to refactor the alertgroup model a bit to more easily achieve this
            {"firing": count, "acknowledged": count, "resolved": count, "silenced": count}
        )
