import logging

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.api.permissions import IsOwner, RBACPermission
from apps.api.serializers.shift_swap import ShiftSwapRequestSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.mobile_app.auth import MobileAppAuthTokenAuthentication
from apps.shift_swaps import exceptions
from apps.shift_swaps.models import ShiftSwapRequest
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import PublicPrimaryKeyMixin
from common.api_helpers.paginators import FiftyPageSizePaginator

logger = logging.getLogger(__name__)


class ShiftSwapView(PublicPrimaryKeyMixin, ModelViewSet):
    authentication_classes = (PluginAuthentication, MobileAppAuthTokenAuthentication)
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        # TODO: add note to public documentation about these permissions also giving access to shift swaps
        # unless we want to make a separate resource type for them?
        "metadata": [RBACPermission.Permissions.SCHEDULES_READ],
        "list": [RBACPermission.Permissions.SCHEDULES_READ],
        "retrieve": [RBACPermission.Permissions.SCHEDULES_READ],
        "create": [RBACPermission.Permissions.SCHEDULES_WRITE],
        "update": [RBACPermission.Permissions.SCHEDULES_WRITE],
        "partial_update": [RBACPermission.Permissions.SCHEDULES_WRITE],
        "destroy": [RBACPermission.Permissions.SCHEDULES_WRITE],
        "take": [RBACPermission.Permissions.SCHEDULES_WRITE],
    }

    is_beneficiary = IsOwner(ownership_field="beneficiary")

    rbac_object_permissions = {
        is_beneficiary: [
            "update",
            "partial_update",
            "destroy",
        ],
    }

    model = ShiftSwapRequest
    serializer_class = ShiftSwapRequestSerializer
    pagination_class = FiftyPageSizePaginator

    def get_queryset(self):
        return ShiftSwapRequest.objects.filter(schedule__organization=self.request.auth.organization)

    @action(methods=["post"], detail=True)
    def take(self, request, pk) -> Response:
        shift_swap = self.get_object()

        try:
            shift_swap.take(request.user)
        except exceptions.ShiftSwapRequestNotOpenForTaking:
            raise BadRequest(detail="The shift swap request is not in a state which allows it to be taken")
        except exceptions.BeneficiaryCannotTakeOwnShiftSwapRequest:
            raise BadRequest(detail="A shift swap request cannot be created and taken by the same user")

        return Response(ShiftSwapRequestSerializer(shift_swap).data, status=status.HTTP_200_OK)
