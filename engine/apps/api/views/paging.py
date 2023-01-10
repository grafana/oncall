from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.alerts.paging import direct_paging
from apps.api.permissions import RBACPermission
from apps.auth_token.auth import PluginAuthentication
from common.api_helpers.exceptions import BadRequest


class DirectPagingAPIView(APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "post": RBACPermission.Permissions.ALERT_GROUPS_WRITE,
    }

    def post(self, request):
        organization = request.auth.organization
        from_user = request.user
        team = from_user.current_team

        if "targets" not in request.data or len(request.data["targets"]) == 0:
            raise BadRequest(detail="No targets provided")

        targets = request.data["targets"]
        force = request.data.get("force", False)

        warnings = []
        for target in targets:
            target_type = target["type"]
            target_id = target["id"]
            important = target["important"]

            if target_type == "user":
                user = organization.users.get(public_primary_key=target_id)
                warning = direct_paging(organization, team, from_user, user=user, important=important, force=force)
            elif target_type == "schedule":
                schedule = organization.oncall_schedules.get(public_primary_key=target_id)
                warning = direct_paging(
                    organization, team, from_user, schedule=schedule, important=important, force=force
                )
            else:
                raise BadRequest(detail=f"Unknown target type: {target_type}")

            # TODO: probably it's better to have a separate method for generating warnings (instead of checking in direct_paging)?
            # TODO: This would help to make sure either all targets are paged or none of them are.
            warnings.append(warning)

        success = len(warnings) == 0
        return Response(data={"success": success, "warnings": warnings})


# TODO: support paging for existing alert groups
# TODO: probably return alert group ID that was created?
# TODO: add escalation chain support
