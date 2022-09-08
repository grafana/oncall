import pytz
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, OuterRef, Subquery
from django.db.utils import IntegrityError
from django.urls import reverse
from django.utils import dateparse, timezone
from django.utils.functional import cached_property
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import Response
from rest_framework.viewsets import ModelViewSet

from apps.alerts.models import EscalationChain
from apps.api.permissions import MODIFY_ACTIONS, READ_ACTIONS, ActionPermission, AnyRole, IsAdmin, IsAdminOrEditor
from apps.api.serializers.schedule_base import ScheduleFastSerializer
from apps.api.serializers.schedule_polymorphic import (
    PolymorphicScheduleCreateSerializer,
    PolymorphicScheduleSerializer,
    PolymorphicScheduleUpdateSerializer,
)
from apps.auth_token.auth import PluginAuthentication
from apps.auth_token.constants import SCHEDULE_EXPORT_TOKEN_NAME
from apps.auth_token.models import ScheduleExportAuthToken
from apps.schedules.models import OnCallSchedule
from apps.slack.models import SlackChannel
from apps.slack.tasks import update_slack_user_group_for_schedules
from common.api_helpers.exceptions import BadRequest, Conflict
from common.api_helpers.mixins import (
    CreateSerializerMixin,
    PublicPrimaryKeyMixin,
    ShortSerializerMixin,
    UpdateSerializerMixin,
)
from common.api_helpers.utils import create_engine_url, get_date_range_from_request
from common.insight_log import EntityEvent, write_resource_insight_log

EVENTS_FILTER_BY_ROTATION = "rotation"
EVENTS_FILTER_BY_OVERRIDE = "override"
EVENTS_FILTER_BY_FINAL = "final"


class ScheduleView(
    PublicPrimaryKeyMixin, ShortSerializerMixin, CreateSerializerMixin, UpdateSerializerMixin, ModelViewSet
):
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
            "filter_events",
            "next_shifts_per_user",
            "notify_empty_oncall_options",
            "notify_oncall_shift_freq_options",
            "mention_options",
            "related_escalation_chains",
        ),
    }
    filter_backends = [SearchFilter]
    search_fields = ("name",)

    queryset = OnCallSchedule.objects.all()
    serializer_class = PolymorphicScheduleSerializer
    create_serializer_class = PolymorphicScheduleCreateSerializer
    update_serializer_class = PolymorphicScheduleUpdateSerializer
    short_serializer_class = ScheduleFastSerializer

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

    def _annotate_queryset(self, queryset):
        """Annotate queryset with additional schedule metadata."""
        organization = self.request.auth.organization
        slack_channels = SlackChannel.objects.filter(
            slack_team_identity=organization.slack_team_identity,
            slack_id=OuterRef("channel"),
        )
        queryset = queryset.annotate(
            slack_channel_name=Subquery(slack_channels.values("name")[:1]),
            slack_channel_pk=Subquery(slack_channels.values("public_primary_key")[:1]),
            num_escalation_chains=Count(
                "escalation_policies__escalation_chain",
                distinct=True,
            ),
        )
        return queryset

    def get_queryset(self):
        is_short_request = self.request.query_params.get("short", "false") == "true"
        organization = self.request.auth.organization
        queryset = OnCallSchedule.objects.filter(
            organization=organization,
            team=self.request.user.current_team,
        )
        if not is_short_request:
            queryset = self._annotate_queryset(queryset)
            queryset = self.serializer_class.setup_eager_loading(queryset)
        return queryset

    def get_object(self):
        # Override this method because we want to get object from organization instead of concrete team.
        pk = self.kwargs["pk"]
        organization = self.request.auth.organization
        queryset = organization.oncall_schedules.filter(
            public_primary_key=pk,
        )
        queryset = self._annotate_queryset(queryset)

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
        serializer.save()
        write_resource_insight_log(instance=serializer.instance, author=self.request.user, event=EntityEvent.CREATED)

    def perform_update(self, serializer):
        prev_state = serializer.instance.insight_logs_serialized
        old_user_group = serializer.instance.user_group
        serializer.save()
        if old_user_group is not None:
            update_slack_user_group_for_schedules.apply_async((old_user_group.pk,))
        if serializer.instance.user_group is not None and serializer.instance.user_group != old_user_group:
            update_slack_user_group_for_schedules.apply_async((serializer.instance.user_group.pk,))
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
        events = schedule.filter_events(user_tz, date, days=1, with_empty=with_empty, with_gap=with_gap)

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
            "events": events,
        }
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def filter_events(self, request, pk):
        user_tz, starting_date, days = get_date_range_from_request(self.request)

        filter_by = self.request.query_params.get("type")
        valid_filters = (EVENTS_FILTER_BY_ROTATION, EVENTS_FILTER_BY_OVERRIDE, EVENTS_FILTER_BY_FINAL)
        if filter_by is not None and filter_by not in valid_filters:
            raise BadRequest(detail="Invalid type value")
        resolve_schedule = filter_by is None or filter_by == EVENTS_FILTER_BY_FINAL

        schedule = self.original_get_object()

        if filter_by is not None and filter_by != EVENTS_FILTER_BY_FINAL:
            filter_by = OnCallSchedule.PRIMARY if filter_by == EVENTS_FILTER_BY_ROTATION else OnCallSchedule.OVERRIDES
            events = schedule.filter_events(
                user_tz, starting_date, days=days, with_empty=True, with_gap=resolve_schedule, filter_by=filter_by
            )
        else:  # return final schedule
            events = schedule.final_events(user_tz, starting_date, days)

        result = {
            "id": schedule.public_primary_key,
            "name": schedule.name,
            "type": PolymorphicScheduleSerializer().to_resource_type(schedule),
            "events": events,
        }
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def next_shifts_per_user(self, request, pk):
        """Return next shift for users in schedule."""
        user_tz, _ = self.get_request_timezone()
        now = timezone.now()
        starting_date = now.date()
        schedule = self.original_get_object()
        events = schedule.final_events(user_tz, starting_date, days=30)

        users = {u: None for u in schedule.related_users()}
        for e in events:
            user = e["users"][0]["pk"] if e["users"] else None
            if user is not None and users.get(user) is None and e["end"] > now:
                users[user] = e

        result = {"users": users}
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def related_escalation_chains(self, request, pk):
        """Return escalation chains associated to schedule."""
        schedule = self.original_get_object()
        escalation_chains = EscalationChain.objects.filter(escalation_policies__notify_schedule=schedule).distinct()

        result = [{"name": e.name, "pk": e.public_primary_key} for e in escalation_chains]
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
                write_resource_insight_log(instance=instance, author=self.request.user, event=EntityEvent.CREATED)
            except IntegrityError:
                raise Conflict("Schedule export token for user already exists")

            export_url = create_engine_url(
                reverse("api-public:schedules-export", kwargs={"pk": schedule.public_primary_key})
                + f"?{SCHEDULE_EXPORT_TOKEN_NAME}={token}"
            )

            data = {"token": token, "created_at": instance.created_at, "export_url": export_url}

            return Response(data, status=status.HTTP_201_CREATED)

        if self.request.method == "DELETE":
            try:
                token = ScheduleExportAuthToken.objects.get(user_id=self.request.user.id, schedule_id=schedule.id)
                write_resource_insight_log(instance=token, author=self.request.user, event=EntityEvent.DELETED)
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
