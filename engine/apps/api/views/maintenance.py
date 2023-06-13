from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.alerts.models import AlertReceiveChannel
from apps.alerts.models.maintainable_object import MaintainableObject
from apps.api.permissions import RBACPermission
from apps.auth_token.auth import PluginAuthentication
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import TeamFilteringMixin
from common.exceptions import MaintenanceCouldNotBeStartedError


class GetObjectMixin:
    def get_object(self, request):
        organization = request.auth.organization
        type = request.data.get("type", None)

        if type == "organization":
            instance = organization
        elif type == "alert_receive_channel":
            pk = request.data.get("alert_receive_channel_id", None)
            if pk is not None:
                try:
                    instance = AlertReceiveChannel.objects.get(
                        public_primary_key=pk,
                        organization=organization,
                    )
                    if instance.team is not None and instance.team not in self.request.user.teams.all():
                        raise BadRequest(detail={"alert_receive_channel_id": ["unknown id"]})
                except AlertReceiveChannel.DoesNotExist:
                    raise BadRequest(detail={"alert_receive_channel_id": ["unknown id"]})
            else:
                raise BadRequest(detail={"alert_receive_channel_id": ["id is required"]})
        else:
            raise BadRequest(detail={"type": ["Unknown type"]})

        return instance


class MaintenanceAPIView(APIView, TeamFilteringMixin):
    """Deprecated. Maintenance management is now performed on integrations page (alert_receive_channel/ endpoint))"""

    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "get": [RBACPermission.Permissions.MAINTENANCE_READ],
        "filters": [RBACPermission.Permissions.MAINTENANCE_READ],
    }

    def get(self, request):
        organization = self.request.auth.organization

        response = []
        integrations_under_maintenance = (
            AlertReceiveChannel.objects.filter(
                maintenance_mode__isnull=False, organization=organization, *self.available_teams_lookup_args
            )
            .distinct()
            .order_by("maintenance_started_at")
        )

        if organization.maintenance_mode is not None:
            response.append(
                {
                    "organization_id": organization.public_primary_key,
                    "type": "organization",
                    "maintenance_mode": organization.maintenance_mode,
                    "maintenance_till_timestamp": organization.till_maintenance_timestamp,
                    "started_at_timestamp": organization.started_at_timestamp,
                }
            )

        for i in integrations_under_maintenance:
            response.append(
                {
                    "alert_receive_channel_id": i.public_primary_key,
                    "type": "alert_receive_channel",
                    "maintenance_mode": i.maintenance_mode,
                    "maintenance_till_timestamp": i.till_maintenance_timestamp,
                    "started_at_timestamp": i.started_at_timestamp,
                }
            )

        return Response(response, status=200)

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

        if filter_name is not None:
            filter_options = list(filter(lambda f: filter_name in f["name"], filter_options))

        return Response(filter_options)


class MaintenanceStartAPIView(GetObjectMixin, APIView):
    """Deprecated. Maintenance management is now performed on integrations page (alert_receive_channel/ endpoint))"""

    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)
    rbac_permissions = {
        "post": [RBACPermission.Permissions.MAINTENANCE_WRITE],
    }

    def post(self, request):
        mode = request.data.get("mode", None)
        duration = request.data.get("duration", None)
        try:
            mode = int(mode)
        except (ValueError, TypeError):
            raise BadRequest(detail={"mode": ["Invalid mode"]})
        if mode not in [MaintainableObject.DEBUG_MAINTENANCE, MaintainableObject.MAINTENANCE]:
            raise BadRequest(detail={"mode": ["Unknown mode"]})
        try:
            duration = int(duration)
        except (ValueError, TypeError):
            raise BadRequest(detail={"duration": ["Invalid duration"]})
        if duration not in MaintainableObject.maintenance_duration_options_in_seconds():
            raise BadRequest(detail={"mode": ["Unknown duration"]})

        instance = self.get_object(request)
        try:
            instance.start_maintenance(mode, duration, request.user)
        except MaintenanceCouldNotBeStartedError as e:
            if type(instance) == AlertReceiveChannel:
                detail = {"alert_receive_channel_id": ["Already on maintenance"]}
            else:
                detail = str(e)
            raise BadRequest(detail=detail)

        return Response(status=status.HTTP_200_OK)


class MaintenanceStopAPIView(GetObjectMixin, APIView):
    """Deprecated. Maintenance management is now performed on integrations page (alert_receive_channel/ endpoint))"""

    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)
    rbac_permissions = {
        "post": [RBACPermission.Permissions.MAINTENANCE_WRITE],
    }

    def post(self, request):
        instance = self.get_object(request)
        user = request.user
        instance.force_disable_maintenance(user)
        return Response(status=status.HTTP_200_OK)
