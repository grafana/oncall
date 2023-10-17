from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.alerts.paging import DirectPagingAlertGroupResolvedError, direct_paging
from apps.api.permissions import RBACPermission
from apps.api.serializers.paging import DirectPagingSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.user_management.models import Team
from common.api_helpers.exceptions import BadRequest


class DirectPagingAPIView(APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "post": [RBACPermission.Permissions.ALERT_GROUPS_DIRECT_PAGING],
    }

    def post(self, request):
        organization = request.auth.organization
        from_user = request.user

        serializer = DirectPagingSerializer(
            data=request.data, context={"organization": organization, "request": request}
        )
        serializer.is_valid(raise_exception=True)

        team: Team | None = serializer.validated_data["team"]

        try:
            alert_group = direct_paging(
                organization=organization,
                from_user=from_user,
                message=serializer.validated_data["message"],
                team=team,
                users=[(user["instance"], user["important"]) for user in serializer.validated_data["users"]],
                alert_group=serializer.validated_data["alert_group"],
            )
        except DirectPagingAlertGroupResolvedError:
            raise BadRequest(detail=DirectPagingAlertGroupResolvedError.DETAIL)

        return Response(data={"alert_group_id": alert_group.public_primary_key}, status=status.HTTP_200_OK)
