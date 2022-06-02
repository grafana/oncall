import datetime
from urllib.parse import urljoin

import pytz
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import OuterRef, Subquery
from django.db.utils import IntegrityError
from django.urls import reverse
from django.utils import dateparse, timezone
from django.utils.functional import cached_property
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import Response
from rest_framework.viewsets import ModelViewSet

from apps.api.permissions import MODIFY_ACTIONS, READ_ACTIONS, ActionPermission, AnyRole, IsAdmin, IsAdminOrEditor
from apps.api.serializers.schedule_polymorphic import (
    PolymorphicScheduleCreateSerializer,
    PolymorphicScheduleSerializer,
    PolymorphicScheduleUpdateSerializer,
)
from apps.auth_token.auth import PluginAuthentication
from apps.auth_token.constants import SCHEDULE_EXPORT_TOKEN_NAME
from apps.auth_token.models import ScheduleExportAuthToken
from apps.schedules.ical_utils import list_of_oncall_shifts_from_ical
from apps.schedules.models import OnCallSchedule
from apps.slack.models import SlackChannel
from apps.slack.tasks import update_slack_user_group_for_schedules
from apps.user_management.organization_log_creator import OrganizationLogType, create_organization_log
from common.api_helpers.exceptions import BadRequest, Conflict
from common.api_helpers.mixins import CreateSerializerMixin, PublicPrimaryKeyMixin, UpdateSerializerMixin


class ScheduleView(PublicPrimaryKeyMixin, CreateSerializerMixin, UpdateSerializerMixin, ModelViewSet):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, ActionPermission)
    action_permissions = {
        IsAdmin: (
            *MODIFY_ACTIONS,
            "reload_ical",
        ),
        IsAdminOrEditor: ("export_token",),
        AnyRole: (
            *READ_ACTIONS,
            "events",
            "notify_empty_oncall_options",
            "notify_oncall_shift_freq_options",
            "mention_options",
        ),
    }

    queryset = OnCallSchedule.objects.all()
    serializer_class = PolymorphicScheduleSerializer
    create_serializer_class = PolymorphicScheduleCreateSerializer
    update_serializer_class = PolymorphicScheduleUpdateSerializer

    @cached_property
    def can_update_user_groups(self):
        """
        This property is needed to be propagated down to serializers,
        since it makes an API call to Slack and the response should be cached.
        """
        slack_team_identity = self.request.auth.organization.slack_team_identity

        if slack_team_identity is None:
            return False

        user_group = slack_team_identity.usergroups.first()
        if user_group is None:
            return False

        return user_group.can_be_updated

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"can_update_user_groups": self.can_update_user_groups})
        return context

    def get_queryset(self):
        organization = self.request.auth.organization
        slack_channels = SlackChannel.objects.filter(
            slack_team_identity=organization.slack_team_identity,
            slack_id=OuterRef("channel"),
        )
        queryset = OnCallSchedule.objects.filter(
            organization=organization,
            team=self.request.user.current_team,
        ).annotate(
            slack_channel_name=Subquery(slack_channels.values("name")[:1]),
            slack_channel_pk=Subquery(slack_channels.values("public_primary_key")[:1]),
        )
        queryset = self.serializer_class.setup_eager_loading(queryset)
        return queryset

    def get_object(self):
        # Override this method because we want to get object from organization instead of concrete team.
        pk = self.kwargs["pk"]
        organization = self.request.auth.organization
        slack_channels = SlackChannel.objects.filter(
            slack_team_identity=organization.slack_team_identity,
            slack_id=OuterRef("channel"),
        )
        queryset = organization.oncall_schedules.filter(public_primary_key=pk,).annotate(
            slack_channel_name=Subquery(slack_channels.values("name")[:1]),
            slack_channel_pk=Subquery(slack_channels.values("public_primary_key")[:1]),
        )

        try:
            obj = queryset.get()
        except ObjectDoesNotExist:
            raise NotFound

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def original_get_object(self):
        return super().get_object()

    def perform_create(self, serializer):
        schedule = serializer.save()
        if schedule.user_group is not None:
            update_slack_user_group_for_schedules.apply_async((schedule.user_group.pk,))
        organization = self.request.auth.organization
        user = self.request.user
        description = f"Schedule {schedule.name} was created"
        create_organization_log(organization, user, OrganizationLogType.TYPE_SCHEDULE_CREATED, description)

    def perform_update(self, serializer):
        organization = self.request.auth.organization
        user = self.request.user
        old_schedule = serializer.instance
        old_state = old_schedule.repr_settings_for_client_side_logging
        old_user_group = serializer.instance.user_group

        updated_schedule = serializer.save()

        if old_user_group is not None:
            update_slack_user_group_for_schedules.apply_async((old_user_group.pk,))

        if updated_schedule.user_group is not None and updated_schedule.user_group != old_user_group:
            update_slack_user_group_for_schedules.apply_async((updated_schedule.user_group.pk,))

        new_state = updated_schedule.repr_settings_for_client_side_logging
        description = f"Schedule {updated_schedule.name} was changed from:\n{old_state}\nto:\n{new_state}"
        create_organization_log(organization, user, OrganizationLogType.TYPE_SCHEDULE_CHANGED, description)

    def perform_destroy(self, instance):
        organization = self.request.auth.organization
        user = self.request.user
        description = f"Schedule {instance.name} was deleted"
        create_organization_log(organization, user, OrganizationLogType.TYPE_SCHEDULE_DELETED, description)
        instance.delete()

        if instance.user_group is not None:
            update_slack_user_group_for_schedules.apply_async((instance.user_group.pk,))

    def get_request_timezone(self):
        user_tz = self.request.query_params.get("user_tz", "UTC")
        try:
            pytz.timezone(user_tz)
        except pytz.exceptions.UnknownTimeZoneError:
            raise BadRequest(detail="Invalid tz format")
        date = timezone.now().date()
        date_param = self.request.query_params.get("date")
        if date_param is not None:
            try:
                date = dateparse.parse_date(date_param)
            except ValueError:
                raise BadRequest(detail="Invalid date format")
            else:
                if date is None:
                    raise BadRequest(detail="Invalid date format")

        return user_tz, date

    @action(detail=True, methods=["get"])
    def events(self, request, pk):
        user_tz, date = self.get_request_timezone()
        with_empty = self.request.query_params.get("with_empty", False) == "true"
        with_gap = self.request.query_params.get("with_gap", False) == "true"
        schedule = self.original_get_object()
        shifts = list_of_oncall_shifts_from_ical(schedule, date, user_tz, with_empty, with_gap) or []
        events_result = []
        # for start, end, users, priority_level, source in shifts:
        for shift in shifts:
            all_day = type(shift["start"]) == datetime.date
            is_gap = shift.get("is_gap", False)
            shift_json = {
                "all_day": all_day,
                "start": shift["start"],
                # fix confusing end date for all-day event
                "end": shift["end"] - timezone.timedelta(days=1) if all_day else shift["end"],
                "users": [
                    {
                        "display_name": user.username,
                        "pk": user.public_primary_key,
                    }
                    for user in shift["users"]
                ],
                "priority_level": shift["priority"] if shift["priority"] != 0 else None,
                "source": shift["source"],
                "calendar_type": shift["calendar_type"],
                "is_empty": len(shift["users"]) == 0 and not is_gap,
                "is_gap": is_gap,
            }
            events_result.append(shift_json)

        slack_channel = (
            {
                "id": schedule.slack_channel_pk,
                "slack_id": schedule.channel,
                "display_name": schedule.slack_channel_name,
            }
            if schedule.channel is not None
            else None
        )

        result = {
            "id": schedule.public_primary_key,
            "name": schedule.name,
            "type": PolymorphicScheduleSerializer().to_resource_type(schedule),
            "slack_channel": slack_channel,
            "events": events_result,
        }
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def type_options(self, request):
        # TODO: check if it needed
        choices = []
        for item in OnCallSchedule.SCHEDULE_CHOICES:
            choices.append({"value": str(item[0]), "display_name": item[1]})
        return Response(choices)

    @action(detail=True, methods=["post"])
    def reload_ical(self, request, pk):
        schedule = self.original_get_object()
        schedule.drop_cached_ical()
        schedule.check_empty_shifts_for_next_week()
        schedule.check_gaps_for_next_week()

        if schedule.user_group is not None:
            update_slack_user_group_for_schedules.apply_async((schedule.user_group.pk,))

        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=["get", "post", "delete"])
    def export_token(self, request, pk):
        schedule = self.original_get_object()

        if self.request.method == "GET":
            try:
                token = ScheduleExportAuthToken.objects.get(user_id=self.request.user.id, schedule_id=schedule.id)
            except ScheduleExportAuthToken.DoesNotExist:
                raise NotFound

            response = {
                "created_at": token.created_at,
                "revoked_at": token.revoked_at,
                "active": token.active,
            }

            return Response(response, status=status.HTTP_200_OK)

        if self.request.method == "POST":
            try:
                instance, token = ScheduleExportAuthToken.create_auth_token(
                    request.user, request.user.organization, schedule
                )
            except IntegrityError:
                raise Conflict("Schedule export token for user already exists")

            export_url = urljoin(
                settings.BASE_URL,
                reverse("api-public:schedules-export", kwargs={"pk": schedule.public_primary_key})
                + f"?{SCHEDULE_EXPORT_TOKEN_NAME}={token}",
            )

            data = {"token": token, "created_at": instance.created_at, "export_url": export_url}

            return Response(data, status=status.HTTP_201_CREATED)

        if self.request.method == "DELETE":
            try:
                token = ScheduleExportAuthToken.objects.get(user_id=self.request.user.id, schedule_id=schedule.id)
                token.delete()
            except ScheduleExportAuthToken.DoesNotExist:
                raise NotFound

            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"])
    def notify_oncall_shift_freq_options(self, request):
        options = []
        for choice in OnCallSchedule.NotifyOnCallShiftFreq.choices:
            options.append(
                {
                    "value": choice[0],
                    "display_name": choice[1],
                }
            )
        return Response(options)

    @action(detail=False, methods=["get"])
    def notify_empty_oncall_options(self, request):
        options = []
        for choice in OnCallSchedule.NotifyEmptyOnCall.choices:
            options.append(
                {
                    "value": choice[0],
                    "display_name": choice[1],
                }
            )
        return Response(options)

    @action(detail=False, methods=["get"])
    def mention_options(self, request):
        options = [
            {
                "value": False,
                "display_name": "Inform in channel without mention",
            },
            {
                "value": True,
                "display_name": "Mention person in slack",
            },
        ]
        return Response(options)
