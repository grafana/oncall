from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.auth_token.auth import ApiTokenAuthentication
from apps.public_api import constants as public_api_constants
from apps.public_api.serializers import CustomOnCallShiftSerializer, CustomOnCallShiftUpdateSerializer
from apps.public_api.throttlers.user_throttle import UserThrottle
from apps.schedules.models import CustomOnCallShift
from apps.user_management.organization_log_creator import OrganizationLogType, create_organization_log
from common.api_helpers.filters import ByTeamFilter
from common.api_helpers.mixins import DemoTokenMixin, RateLimitHeadersMixin, UpdateSerializerMixin
from common.api_helpers.paginators import FiftyPageSizePaginator


class CustomOnCallShiftView(RateLimitHeadersMixin, DemoTokenMixin, UpdateSerializerMixin, ModelViewSet):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    throttle_classes = [UserThrottle]

    model = CustomOnCallShift
    serializer_class = CustomOnCallShiftSerializer
    update_serializer_class = CustomOnCallShiftUpdateSerializer

    pagination_class = FiftyPageSizePaginator

    filter_backends = [DjangoFilterBackend]
    filterset_class = ByTeamFilter

    demo_default_id = public_api_constants.DEMO_ON_CALL_SHIFT_ID_1

    def get_queryset(self):
        name = self.request.query_params.get("name", None)
        schedule_id = self.request.query_params.get("schedule_id", None)

        queryset = CustomOnCallShift.objects.filter(organization=self.request.auth.organization)

        if schedule_id:
            queryset = queryset.filter(schedules__public_primary_key=schedule_id)
        if name:
            queryset = queryset.filter(name=name)
        return queryset.order_by("schedules")

    def get_object(self):
        public_primary_key = self.kwargs["pk"]

        try:
            return CustomOnCallShift.objects.filter(
                organization=self.request.auth.organization,
            ).get(public_primary_key=public_primary_key)
        except CustomOnCallShift.DoesNotExist:
            raise NotFound

    def perform_create(self, serializer):
        serializer.save()
        instance = serializer.instance
        organization = self.request.auth.organization
        user = self.request.user
        description = (
            f"Custom on-call shift with params: {instance.repr_settings_for_client_side_logging} " f"was created"
        )
        create_organization_log(organization, user, OrganizationLogType.TYPE_ON_CALL_SHIFT_CREATED, description)

    def perform_update(self, serializer):
        organization = self.request.auth.organization
        user = self.request.user
        old_state = serializer.instance.repr_settings_for_client_side_logging
        serializer.save()
        new_state = serializer.instance.repr_settings_for_client_side_logging
        description = f"Settings of custom on-call shift was changed " f"from:\n{old_state}\nto:\n{new_state}"
        create_organization_log(organization, user, OrganizationLogType.TYPE_ON_CALL_SHIFT_CHANGED, description)

    def perform_destroy(self, instance):
        organization = self.request.auth.organization
        user = self.request.user
        description = (
            f"Custom on-call shift " f"with params: {instance.repr_settings_for_client_side_logging} was deleted"
        )
        create_organization_log(organization, user, OrganizationLogType.TYPE_ON_CALL_SHIFT_DELETED, description)
        instance.delete()
