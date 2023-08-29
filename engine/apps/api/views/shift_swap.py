import logging

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.viewsets import ModelViewSet

from apps.api.permissions import AuthenticatedRequest, IsOwner, RBACPermission
from apps.api.serializers.shift_swap import ShiftSwapRequestListSerializer, ShiftSwapRequestSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.mobile_app.auth import MobileAppAuthTokenAuthentication
from apps.schedules import exceptions
from apps.schedules.models import ShiftSwapRequest
from apps.schedules.tasks.shift_swaps import create_shift_swap_request_message, update_shift_swap_request_message
from apps.user_management.models import User
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import PublicPrimaryKeyMixin
from common.api_helpers.paginators import FiftyPageSizePaginator
from common.insight_log import EntityEvent, write_resource_insight_log

logger = logging.getLogger(__name__)


class BaseShiftSwapViewSet(ModelViewSet):
    model = ShiftSwapRequest
    serializer_class = ShiftSwapRequestSerializer
    pagination_class = FiftyPageSizePaginator

    def _do_create(self, beneficiary: User, serializer: BaseSerializer[ShiftSwapRequest]) -> None:
        shift_swap_request = serializer.save(beneficiary=beneficiary)

        write_resource_insight_log(instance=shift_swap_request, author=self.request.user, event=EntityEvent.CREATED)

        create_shift_swap_request_message.apply_async((shift_swap_request.pk,))

    def _do_take(self, benefactor: User) -> dict:
        shift_swap = self.get_object()

        try:
            shift_swap.take(benefactor)
        except exceptions.ShiftSwapRequestNotOpenForTaking:
            raise BadRequest(detail="The shift swap request is not in a state which allows it to be taken")
        except exceptions.BeneficiaryCannotTakeOwnShiftSwapRequest:
            raise BadRequest(detail="A shift swap request cannot be created and taken by the same user")

        update_shift_swap_request_message.apply_async((shift_swap.pk,))

        return ShiftSwapRequestSerializer(shift_swap).data

    def get_serializer_class(self):
        return ShiftSwapRequestListSerializer if self.action == "list" else super().get_serializer_class()

    def get_queryset(self):
        queryset = ShiftSwapRequest.objects.filter(schedule__organization=self.request.auth.organization)
        return self.serializer_class.setup_eager_loading(queryset)

    def perform_destroy(self, instance: ShiftSwapRequest) -> None:
        # TODO: should we allow deleting a taken request?

        super().perform_destroy(instance)
        write_resource_insight_log(instance=instance, author=self.request.user, event=EntityEvent.DELETED)

        update_shift_swap_request_message.apply_async((instance.pk,))

    def perform_create(self, serializer: BaseSerializer[ShiftSwapRequest]) -> None:
        # default to create swap request with logged in user as beneficiary
        self._do_create(self.request.user, serializer=serializer)

    def perform_update(self, serializer: BaseSerializer[ShiftSwapRequest]) -> None:
        prev_state = serializer.instance.insight_logs_serialized
        serializer.save()
        shift_swap_request = serializer.instance

        write_resource_insight_log(
            instance=shift_swap_request,
            author=self.request.user,
            event=EntityEvent.UPDATED,
            prev_state=prev_state,
            new_state=shift_swap_request.insight_logs_serialized,
        )

        update_shift_swap_request_message.apply_async((shift_swap_request.pk,))


class ShiftSwapViewSet(PublicPrimaryKeyMixin[ShiftSwapRequest], BaseShiftSwapViewSet):
    authentication_classes = (MobileAppAuthTokenAuthentication, PluginAuthentication)
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
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

    @action(methods=["post"], detail=True)
    def take(self, request: AuthenticatedRequest, pk: str) -> Response:
        serialized_shift_swap = self._do_take(benefactor=request.user)
        return Response(serialized_shift_swap, status=status.HTTP_200_OK)
