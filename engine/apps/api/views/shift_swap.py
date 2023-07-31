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
from apps.schedules import exceptions
from apps.schedules.models import ShiftSwapRequest
from apps.schedules.tasks.shift_swaps import create_shift_swap_request_message, update_shift_swap_request_message
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import PublicPrimaryKeyMixin
from common.api_helpers.paginators import FiftyPageSizePaginator
from common.insight_log import EntityEvent, write_resource_insight_log

logger = logging.getLogger(__name__)


class ShiftSwapViewSet(PublicPrimaryKeyMixin, ModelViewSet):
    authentication_classes = (MobileAppAuthTokenAuthentication, PluginAuthentication)
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
        "shifts": [RBACPermission.Permissions.SCHEDULES_READ],
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
        queryset = ShiftSwapRequest.objects.filter(schedule__organization=self.request.auth.organization)
        return self.serializer_class.setup_eager_loading(queryset)

    def perform_destroy(self, instance) -> None:
        # TODO: should we allow deleting a taken request? if so we will have to undo the overrides that were generated

        super().perform_destroy(instance)
        write_resource_insight_log(instance=instance, author=self.request.user, event=EntityEvent.DELETED)

        update_shift_swap_request_message.apply_async((instance.pk,))

    def perform_create(self, serializer) -> None:
        beneficiary = self.request.user
        shift_swap_request = serializer.save(beneficiary=beneficiary)

        write_resource_insight_log(instance=shift_swap_request, author=beneficiary, event=EntityEvent.CREATED)

        create_shift_swap_request_message.apply_async((shift_swap_request.pk,))

    def perform_update(self, serializer) -> None:
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

    @action(methods=["get"], detail=True)
    def shifts(self, request, pk) -> Response:
        shift_swap = self.get_object()
        result = {"events": shift_swap.shifts()}

        return Response(result, status=status.HTTP_200_OK)

    # test: return shifts for swap

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
