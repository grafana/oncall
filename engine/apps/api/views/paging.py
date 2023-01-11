from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.alerts.paging import check_user_availability, direct_paging, unpage_user
from apps.api.permissions import RBACPermission
from apps.api.serializers.paging import CheckUserAvailabilitySerializer, DirectPagingSerializer, UnpageUserSerializer
from apps.auth_token.auth import PluginAuthentication


class CheckUserAvailability(APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "get": [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
    }

    def get(self, request):
        organization = request.auth.organization
        team = request.user.current_team

        serializer = CheckUserAvailabilitySerializer(data=request.data, context={"organization": organization})
        serializer.is_valid(raise_exception=True)

        warnings = check_user_availability(user=serializer.validated_data["user"], team=team)
        return Response(data=warnings, status=status.HTTP_200_OK)


class DirectPagingAPIView(APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "post": [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
    }

    def post(self, request):
        organization = request.auth.organization
        from_user = request.user
        team = from_user.current_team

        serializer = DirectPagingSerializer(data=request.data, context={"organization": organization})
        serializer.is_valid(raise_exception=True)

        users = [(user["instance"], user["important"]) for user in serializer.validated_data["users"]]
        schedules = [
            (schedule["instance"], schedule["important"]) for schedule in serializer.validated_data["schedules"]
        ]

        direct_paging(
            organization=organization,
            team=team,
            from_user=from_user,
            title=serializer.validated_data["title"],
            message=serializer.validated_data["message"],
            users=users,
            schedules=schedules,
            alert_group=serializer.validated_data["alert_group"],
        )

        return Response(status=status.HTTP_200_OK)


class UnpageUserAPIView(APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "post": [RBACPermission.Permissions.ALERT_GROUPS_WRITE],
    }

    def post(self, request):
        organization = request.auth.organization
        from_user = request.user

        serializer = UnpageUserSerializer(data=request.data, context={"organization": organization})
        serializer.is_valid(raise_exception=True)

        unpage_user(
            alert_group=serializer.validated_data["alert_group"],
            user=serializer.validated_data["user"],
            from_user=from_user,
        )

        return Response(status=status.HTTP_200_OK)
