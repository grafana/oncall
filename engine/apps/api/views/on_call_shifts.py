import datetime

import pytz
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.api.permissions import RBACPermission
from apps.api.serializers.on_call_shifts import OnCallShiftSerializer, OnCallShiftUpdateSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.schedules.models import CustomOnCallShift
from common.api_helpers.mixins import PublicPrimaryKeyMixin, TeamFilteringMixin, UpdateSerializerMixin
from common.api_helpers.paginators import FiftyPageSizePaginator
from common.api_helpers.utils import get_date_range_from_request
from common.insight_log import EntityEvent, write_resource_insight_log


class OnCallShiftView(TeamFilteringMixin, PublicPrimaryKeyMixin, UpdateSerializerMixin, ModelViewSet):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "metadata": [RBACPermission.Permissions.SCHEDULES_READ],
        "list": [RBACPermission.Permissions.SCHEDULES_READ],
        "retrieve": [RBACPermission.Permissions.SCHEDULES_READ],
        "details": [RBACPermission.Permissions.SCHEDULES_READ],
        "frequency_options": [RBACPermission.Permissions.SCHEDULES_READ],
        "days_options": [RBACPermission.Permissions.SCHEDULES_READ],
        "create": [RBACPermission.Permissions.SCHEDULES_WRITE],
        "update": [RBACPermission.Permissions.SCHEDULES_WRITE],
        "partial_update": [RBACPermission.Permissions.SCHEDULES_WRITE],
        "destroy": [RBACPermission.Permissions.SCHEDULES_WRITE],
        "preview": [RBACPermission.Permissions.SCHEDULES_WRITE],
    }

    model = CustomOnCallShift
    serializer_class = OnCallShiftSerializer
    update_serializer_class = OnCallShiftUpdateSerializer

    pagination_class = FiftyPageSizePaginator

    filter_backends = [DjangoFilterBackend]

    def get_queryset(self, ignore_filtering_by_available_teams=False):
        schedule_id = self.request.query_params.get("schedule_id", None)
        lookup_kwargs = Q()
        if schedule_id:
            lookup_kwargs = Q(
                Q(schedule__public_primary_key=schedule_id) | Q(schedules__public_primary_key=schedule_id)
            )

        queryset = CustomOnCallShift.objects.filter(
            lookup_kwargs,
            organization=self.request.auth.organization,
        )

        if not ignore_filtering_by_available_teams:
            queryset = queryset.filter(*self.available_teams_lookup_args).distinct()

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
        force_update = self.request.query_params.get("force", "") == "true"
        serializer.save(force_update=force_update)
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
        force = self.request.query_params.get("force", "") == "true"
        instance.delete(force=force)

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

        pytz_tz = pytz.timezone(user_tz)
        datetime_start = datetime.datetime.combine(starting_date, datetime.time.min, tzinfo=pytz_tz)
        datetime_end = datetime_start + datetime.timedelta(days=days)

        shift_events, final_events = schedule.preview_shift(
            shift, datetime_start, datetime_end, updated_shift_pk=updated_shift_pk
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
