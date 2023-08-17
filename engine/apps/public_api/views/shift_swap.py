import logging

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from apps.api.permissions import AuthenticatedRequest
from apps.api.views.shift_swap import BaseShiftSwapViewSet
from apps.auth_token.auth import ApiTokenAuthentication
from apps.public_api.throttlers.user_throttle import UserThrottle
from apps.schedules.models import ShiftSwapRequest
from apps.user_management.models import User
from common.api_helpers.custom_fields import TimeZoneAwareDatetimeField
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import RateLimitHeadersMixin

logger = logging.getLogger(__name__)


class ShiftSwapViewSet(RateLimitHeadersMixin, BaseShiftSwapViewSet):
    # set authentication and permission classes
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    # public API customizations
    throttle_classes = [UserThrottle]

    def get_queryset(self):
        schedule_id = self.request.query_params.get("schedule_id", None)
        beneficiary = self.request.query_params.get("beneficiary", None)
        benefactor = self.request.query_params.get("benefactor", None)
        starting_after = self.request.query_params.get("starting_after", None)
        open_only = self.request.query_params.get("open_only", "false") == "true"

        now = timezone.now()
        if starting_after:
            f = TimeZoneAwareDatetimeField()
            # trigger datetime format validation
            # will raise ValidationError if invalid timestamp is provided
            starting_after = f.to_internal_value(starting_after)
        else:
            starting_after = now

        # base queryset filters by organization
        queryset = super().get_queryset()
        queryset = queryset.filter(swap_start__gte=starting_after)

        if schedule_id:
            queryset = queryset.filter(schedule__public_primary_key=schedule_id)

        if beneficiary:
            queryset = queryset.filter(beneficiary__public_primary_key=beneficiary)

        if benefactor:
            queryset = queryset.filter(benefactor__public_primary_key=benefactor)

        if benefactor:
            queryset = queryset.filter(benefactor__public_primary_key=benefactor)

        if open_only:
            queryset = queryset.filter(benefactor__isnull=True, deleted_at__isnull=True, swap_start__gt=now)

        return queryset.order_by("swap_start")

    def get_object(self):
        public_primary_key = self.kwargs["pk"]
        try:
            return self.get_queryset().get(public_primary_key=public_primary_key)
        except ShiftSwapRequest.DoesNotExist:
            raise NotFound

    def _get_user(self, field_name: str):
        """Require and return user from ID given by field_name."""
        user_pk = self.request.data.pop(field_name, None)
        if not user_pk:
            raise BadRequest(detail=f"{field_name} user ID is required")
        try:
            user = User.objects.get(organization=self.request.auth.organization, public_primary_key=user_pk)
        except User.DoesNotExist:
            raise BadRequest(detail=f"Invalid {field_name} user ID")
        return user

    def perform_create(self, serializer: BaseSerializer[ShiftSwapRequest]) -> None:
        beneficiary = self._get_user("beneficiary")
        self._do_create(beneficiary=beneficiary, serializer=serializer)

    @action(methods=["post"], detail=True)
    def take(self, request: AuthenticatedRequest, pk: str) -> Response:
        # check the swap request exists and it's accessible
        self.get_object()
        benefactor = self._get_user("benefactor")
        serialized_shift_swap = self._do_take(benefactor=benefactor)
        return Response(serialized_shift_swap, status=status.HTTP_200_OK)
