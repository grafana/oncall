from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.api.permissions import MODIFY_ACTIONS, READ_ACTIONS, ActionPermission, AnyRole, IsAdmin
from apps.api.serializers.on_call_shifts import OnCallShiftSerializer, OnCallShiftUpdateSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.schedules.models import CustomOnCallShift
from apps.user_management.organization_log_creator import OrganizationLogType, create_organization_log
from common.api_helpers.mixins import PublicPrimaryKeyMixin, UpdateSerializerMixin
from common.api_helpers.paginators import FiftyPageSizePaginator


class OnCallShiftView(PublicPrimaryKeyMixin, UpdateSerializerMixin, ModelViewSet):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, ActionPermission)

    action_permissions = {
        IsAdmin: MODIFY_ACTIONS,
        AnyRole: (*READ_ACTIONS, "details", "frequency_options", "days_options"),
    }

    model = CustomOnCallShift
    serializer_class = OnCallShiftSerializer
    update_serializer_class = OnCallShiftUpdateSerializer

    pagination_class = FiftyPageSizePaginator

    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        schedule_id = self.request.query_params.get("schedule_id", None)
        lookup_kwargs = Q()
        if schedule_id:
            lookup_kwargs = Q(
                Q(schedule__public_primary_key=schedule_id) | Q(schedules__public_primary_key=schedule_id)
            )

        queryset = CustomOnCallShift.objects.filter(
            lookup_kwargs,
            organization=self.request.auth.organization,
            team=self.request.user.current_team,
        )

        queryset = self.serializer_class.setup_eager_loading(queryset)
        return queryset.order_by("schedules")

    def perform_create(self, serializer):
        serializer.save()
        instance = serializer.instance
        organization = self.request.auth.organization
        user = self.request.user
        description = (
            f"Custom on-call shift with params: {instance.repr_settings_for_client_side_logging} "
            f"was created"  # todo
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

    @action(detail=False, methods=["get"])
    def frequency_options(self, request):
        return Response(
            [
                {
                    "display_name": display_name,
                    "value": freq,
                }
                for freq, display_name in CustomOnCallShift.WEB_FREQUENCY_CHOICES_MAP.items()
            ]
        )

    @action(detail=False, methods=["get"])
    def days_options(self, request):
        return Response(
            [
                {
                    "display_name": display_name,
                    "value": day_number,
                }
                for day_number, display_name in CustomOnCallShift.WEEKDAY_CHOICES
            ]
        )
