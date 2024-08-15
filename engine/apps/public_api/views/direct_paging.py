from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.alerts.paging import DirectPagingAlertGroupResolvedError, DirectPagingUserTeamValidationError, direct_paging
from apps.auth_token.auth import ApiTokenAuthentication
from apps.public_api.serializers.direct_paging import DirectPagingSerializer
from apps.public_api.throttlers import UserThrottle
from common.api_helpers.exceptions import BadRequest


class DirectPagingView(APIView):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    throttle_classes = [UserThrottle]

    def post(self, request):
        user = request.user
        organization = user.organization

        serializer = DirectPagingSerializer(
            data=request.data, context={"organization": organization, "request": request}
        )
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        try:
            alert_group = direct_paging(
                organization=organization,
                from_user=user,
                message=validated_data["message"],
                title=validated_data["title"],
                source_url=validated_data["source_url"],
                team=validated_data["team"],
                users=[(user["instance"], user["important"]) for user in validated_data["users"]],
                alert_group=validated_data["alert_group"],
            )
        except DirectPagingAlertGroupResolvedError:
            raise BadRequest(detail=DirectPagingAlertGroupResolvedError.DETAIL)
        except DirectPagingUserTeamValidationError:
            raise BadRequest(detail=DirectPagingUserTeamValidationError.DETAIL)

        return Response(data={"alert_group_id": alert_group.public_primary_key}, status=status.HTTP_200_OK)
