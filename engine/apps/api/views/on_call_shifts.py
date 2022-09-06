from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.api.permissions import MODIFY_ACTIONS, READ_ACTIONS, ActionPermission, AnyRole, IsAdmin
from apps.api.serializers.on_call_shifts import OnCallShiftSerializer, OnCallShiftUpdateSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.schedules.models import CustomOnCallShift
from common.api_helpers.mixins import PublicPrimaryKeyMixin, UpdateSerializerMixin
from common.api_helpers.paginators import FiftyPageSizePaginator
from common.api_helpers.utils import get_date_range_from_request
from common.insight_log import EntityEvent, write_resource_insight_log


class OnCallShiftView(PublicPrimaryKeyMixin, UpdateSerializerMixin, ModelViewSet):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, ActionPermission)

    action_permissions = {
        IsAdmin: (*MODIFY_ACTIONS, "preview"),
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
        write_resource_insight_log(
            instance=serializer.instance,
            author=self.request.user,
            event=EntityEvent.DELETED,
        )

    def perform_update(self, serializer):
        prev_state = serializer.instance.insight_logs_serialized
        serializer.save()
        new_state = serializer.instance.insight_logs_serialized
        write_resource_insight_log(
            instance=serializer.instance,
            author=self.request.user,
            event=EntityEvent.UPDATED,
            prev_state=prev_state,
            new_state=new_state,
        )

    def perform_destroy(self, instance):
        write_resource_insight_log(
            instance=instance,
            author=self.request.user,
            event=EntityEvent.DELETED,
        )
        instance.delete()

    @action(detail=False, methods=["post"])
    def preview(self, request):
        user_tz, starting_date, days = get_date_range_from_request(self.request)

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer._correct_validated_data(
            serializer.validated_data["type"], serializer.validated_data
        )

        updated_shift_pk = self.request.data.get("shift_pk")
        shift = CustomOnCallShift(**validated_data)
        schedule = shift.schedule
        shift_events, final_events = schedule.preview_shift(
            shift, user_tz, starting_date, days, updated_shift_pk=updated_shift_pk
        )
        data = {
            "rotation": shift_events,
            "final": final_events,
        }
        return Response(data=data, status=status.HTTP_200_OK)

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
                    "value": value,
                }
                for value, display_name in CustomOnCallShift.WEB_WEEKDAY_MAP.items()
            ]
        )
