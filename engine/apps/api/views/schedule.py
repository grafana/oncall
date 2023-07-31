import datetime
import functools
import operator

import pytz
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, OuterRef, Subquery
from django.db.utils import IntegrityError
from django.urls import reverse
from django.utils import dateparse, timezone
from django.utils.functional import cached_property
from django_filters import rest_framework as filters
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.fields import BooleanField
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import Response
from rest_framework.viewsets import ModelViewSet

from apps.alerts.models import EscalationChain, EscalationPolicy
from apps.api.permissions import RBACPermission
from apps.api.serializers.schedule_base import ScheduleFastSerializer
from apps.api.serializers.schedule_polymorphic import (
    PolymorphicScheduleCreateSerializer,
    PolymorphicScheduleSerializer,
    PolymorphicScheduleUpdateSerializer,
)
from apps.api.serializers.shift_swap import ShiftSwapRequestSerializer
from apps.api.serializers.user import ScheduleUserSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.auth_token.constants import SCHEDULE_EXPORT_TOKEN_NAME
from apps.auth_token.models import ScheduleExportAuthToken
from apps.mobile_app.auth import MobileAppAuthTokenAuthentication
from apps.schedules.models import OnCallSchedule
from apps.slack.models import SlackChannel
from apps.slack.tasks import update_slack_user_group_for_schedules
from common.api_helpers.exceptions import BadRequest, Conflict
from common.api_helpers.filters import ByTeamModelFieldFilterMixin, ModelFieldFilterMixin, TeamModelMultipleChoiceFilter
from common.api_helpers.mixins import (
    CreateSerializerMixin,
    PublicPrimaryKeyMixin,
    ShortSerializerMixin,
    TeamFilteringMixin,
    UpdateSerializerMixin,
)
from common.api_helpers.paginators import FifteenPageSizePaginator
from common.api_helpers.utils import create_engine_url, get_date_range_from_request
from common.insight_log import EntityEvent, write_resource_insight_log
from common.timezones import raise_exception_if_not_valid_timezone

EVENTS_FILTER_BY_ROTATION = "rotation"
EVENTS_FILTER_BY_OVERRIDE = "override"
EVENTS_FILTER_BY_FINAL = "final"

SCHEDULE_TYPE_TO_CLASS = {
    str(num_type): cls for cls, num_type in PolymorphicScheduleSerializer.SCHEDULE_CLASS_TO_TYPE.items()
}


class ScheduleFilter(ByTeamModelFieldFilterMixin, ModelFieldFilterMixin, filters.FilterSet):
    team = TeamModelMultipleChoiceFilter()


class ScheduleView(
    TeamFilteringMixin,
    PublicPrimaryKeyMixin,
    ShortSerializerMixin,
    CreateSerializerMixin,
    UpdateSerializerMixin,
    ModelViewSet,
    mixins.ListModelMixin,
):
    authentication_classes = (
        MobileAppAuthTokenAuthentication,
        PluginAuthentication,
    )
    permission_classes = (IsAuthenticated, RBACPermission)
    rbac_permissions = {
        "metadata": [RBACPermission.Permissions.SCHEDULES_READ],
        "list": [RBACPermission.Permissions.SCHEDULES_READ],
        "retrieve": [RBACPermission.Permissions.SCHEDULES_READ],
        "events": [RBACPermission.Permissions.SCHEDULES_READ],
        "filter_events": [RBACPermission.Permissions.SCHEDULES_READ],
        "filter_shift_swaps": [RBACPermission.Permissions.SCHEDULES_READ],
        "next_shifts_per_user": [RBACPermission.Permissions.SCHEDULES_READ],
        "related_users": [RBACPermission.Permissions.SCHEDULES_READ],
        "quality": [RBACPermission.Permissions.SCHEDULES_READ],
        "notify_empty_oncall_options": [RBACPermission.Permissions.SCHEDULES_READ],
        "notify_oncall_shift_freq_options": [RBACPermission.Permissions.SCHEDULES_READ],
        "mention_options": [RBACPermission.Permissions.SCHEDULES_READ],
        "related_escalation_chains": [RBACPermission.Permissions.SCHEDULES_READ],
        "create": [RBACPermission.Permissions.SCHEDULES_WRITE],
        "update": [RBACPermission.Permissions.SCHEDULES_WRITE],
        "partial_update": [RBACPermission.Permissions.SCHEDULES_WRITE],
        "destroy": [RBACPermission.Permissions.SCHEDULES_WRITE],
        "reload_ical": [RBACPermission.Permissions.SCHEDULES_WRITE],
        "export_token": [RBACPermission.Permissions.SCHEDULES_EXPORT],
        "filters": [RBACPermission.Permissions.SCHEDULES_READ],
    }

    filter_backends = [SearchFilter, filters.DjangoFilterBackend]
    search_fields = ("name",)
    filterset_class = ScheduleFilter

    queryset = OnCallSchedule.objects.all()
    serializer_class = PolymorphicScheduleSerializer
    create_serializer_class = PolymorphicScheduleCreateSerializer
    update_serializer_class = PolymorphicScheduleUpdateSerializer
    short_serializer_class = ScheduleFastSerializer
    pagination_class = FifteenPageSizePaginator

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

    @cached_property
    def oncall_users(self):
        """
        The result of this method is cached and is reused for the whole lifetime of a request,
        since self.get_serializer_context() is called multiple times for every instance in the queryset.
        """
        current_page_schedules = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        pks = [schedule.pk for schedule in current_page_schedules]
        queryset = OnCallSchedule.objects.filter(pk__in=pks)
        return queryset.get_oncall_users()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"can_update_user_groups": self.can_update_user_groups})
        context.update({"oncall_users": self.oncall_users})
        return context

    def _annotate_queryset(self, queryset):
        """Annotate queryset with additional schedule metadata."""
        organization = self.request.auth.organization
        slack_channels = SlackChannel.objects.filter(
            slack_team_identity=organization.slack_team_identity,
            slack_id=OuterRef("channel"),
        )
        escalation_policies = (
            EscalationPolicy.objects.values("notify_schedule")
            .order_by("notify_schedule")
            .annotate(num_escalation_chains=Count("notify_schedule"))
            .filter(notify_schedule=OuterRef("id"))
        )
        queryset = queryset.annotate(
            slack_channel_name=Subquery(slack_channels.values("name")[:1]),
            slack_channel_pk=Subquery(slack_channels.values("public_primary_key")[:1]),
            num_escalation_chains=Subquery(escalation_policies.values("num_escalation_chains")[:1]),
        )
        return queryset

    def get_queryset(self, ignore_filtering_by_available_teams=False):
        is_short_request = self.request.query_params.get("short", "false") == "true"
        filter_by_type = self.request.query_params.getlist("type")
        mine = BooleanField(allow_null=True).to_internal_value(data=self.request.query_params.get("mine"))
        used = BooleanField(allow_null=True).to_internal_value(data=self.request.query_params.get("used"))
        organization = self.request.auth.organization
        queryset = OnCallSchedule.objects.filter(organization=organization).defer(
            # avoid requesting large text fields which are not used when listing schedules
            "prev_ical_file_primary",
            "prev_ical_file_overrides",
            "cached_ical_final_schedule",
        )
        if not ignore_filtering_by_available_teams:
            queryset = queryset.filter(*self.available_teams_lookup_args).distinct()
        if not is_short_request:
            queryset = self._annotate_queryset(queryset)
            queryset = self.serializer_class.setup_eager_loading(queryset)
        if filter_by_type:
            valid_types = [i for i in filter_by_type if i in SCHEDULE_TYPE_TO_CLASS]
            if valid_types:
                queryset = functools.reduce(
                    operator.or_, [queryset.filter().instance_of(SCHEDULE_TYPE_TO_CLASS[i]) for i in valid_types]
                )
        if used is not None:
            queryset = queryset.filter(escalation_policies__isnull=not used).distinct()
        if mine:
            user = self.request.user
            queryset = queryset.related_to_user(user)

        queryset = queryset.order_by("pk")
        return queryset

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

    def get_object(self) -> OnCallSchedule:
        # get the object from the whole organization if there is a flag `get_from_organization=true`
        # otherwise get the object from the current team
        get_from_organization: bool = self.request.query_params.get("from_organization", "false") == "true"
        if get_from_organization:
            return self.get_object_from_organization()
        return super().get_object()

    def get_object_from_organization(self, ignore_filtering_by_available_teams=False):
        # use this method to get the object from the whole organization instead of the current team
        pk = self.kwargs["pk"]
        organization = self.request.auth.organization
        queryset = organization.oncall_schedules.filter(
            public_primary_key=pk,
        )
        if not ignore_filtering_by_available_teams:
            queryset = queryset.filter(*self.available_teams_lookup_args).distinct()
        queryset = self._annotate_queryset(queryset)

        try:
            obj = queryset.get()
        except ObjectDoesNotExist:
            raise NotFound

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def get_request_timezone(self):
        user_tz = self.request.query_params.get("user_tz", "UTC")
        raise_exception_if_not_valid_timezone(user_tz)

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
        user_tz, starting_date = self.get_request_timezone()
        with_empty = self.request.query_params.get("with_empty", False) == "true"
        with_gap = self.request.query_params.get("with_gap", False) == "true"

        schedule = self.get_object()

        pytz_tz = pytz.timezone(user_tz)
        datetime_start = datetime.datetime.combine(starting_date, datetime.time.min, tzinfo=pytz_tz)
        datetime_end = datetime_start + datetime.timedelta(days=1)
        events = schedule.filter_events(datetime_start, datetime_end, with_empty=with_empty, with_gap=with_gap)

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
    def filter_events(self, request: Request, pk: str) -> Response:
        user_tz, starting_date, days = get_date_range_from_request(self.request)

        filter_by: str | None = self.request.query_params.get("type")
        valid_filters = (EVENTS_FILTER_BY_ROTATION, EVENTS_FILTER_BY_OVERRIDE, EVENTS_FILTER_BY_FINAL)
        if filter_by is not None and filter_by not in valid_filters:
            raise BadRequest(detail="Invalid type value")
        resolve_schedule = filter_by is None or filter_by == EVENTS_FILTER_BY_FINAL

        schedule = self.get_object()

        pytz_tz = pytz.timezone(user_tz)
        datetime_start = datetime.datetime.combine(starting_date, datetime.time.min, tzinfo=pytz_tz)
        datetime_end = datetime_start + datetime.timedelta(days=days)

        if filter_by is not None and filter_by != EVENTS_FILTER_BY_FINAL:
            filter_by = OnCallSchedule.PRIMARY if filter_by == EVENTS_FILTER_BY_ROTATION else OnCallSchedule.OVERRIDES
            events = schedule.filter_events(
                datetime_start,
                datetime_end,
                with_empty=True,
                with_gap=resolve_schedule,
                filter_by=filter_by,
                all_day_datetime=True,
            )
        else:  # return final schedule
            events = schedule.final_events(datetime_start, datetime_end)

        result = {
            "id": schedule.public_primary_key,
            "name": schedule.name,
            "type": PolymorphicScheduleSerializer().to_resource_type(schedule),
            "events": events,
        }
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def filter_shift_swaps(self, request: Request, pk: str) -> Response:
        user_tz, starting_date, days = get_date_range_from_request(self.request)
        schedule = self.get_object()

        pytz_tz = pytz.timezone(user_tz)
        datetime_start = datetime.datetime.combine(starting_date, datetime.time.min, tzinfo=pytz_tz)
        datetime_end = datetime_start + datetime.timedelta(days=days)

        swap_requests = schedule.filter_swap_requests(datetime_start, datetime_end)

        serialized_swap_requests = ShiftSwapRequestSerializer(swap_requests, many=True)
        result = {"shift_swaps": serialized_swap_requests.data}

        return Response(result, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def next_shifts_per_user(self, request, pk):
        """Return next shift for users in schedule."""
        now = timezone.now()
        datetime_end = now + datetime.timedelta(days=30)
        schedule = self.get_object()

        events = schedule.final_events(now, datetime_end)

        users = {u.public_primary_key: None for u in schedule.related_users()}
        for e in events:
            user = e["users"][0]["pk"] if e["users"] else None
            if user is not None and users.get(user) is None and e["end"] > now:
                users[user] = e

        result = {"users": users}
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def related_users(self, request, pk):
        schedule = self.get_object()
        serializer = ScheduleUserSerializer(schedule.related_users(), many=True)
        result = {"users": serializer.data}
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def related_escalation_chains(self, request, pk):
        """Return escalation chains associated to schedule."""
        schedule = self.get_object()
        escalation_chains = EscalationChain.objects.filter(escalation_policies__notify_schedule=schedule).distinct()

        result = [{"name": e.name, "pk": e.public_primary_key} for e in escalation_chains]
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def quality(self, request, pk):
        schedule = self.get_object()

        _, date = self.get_request_timezone()
        datetime_start = datetime.datetime.combine(date, datetime.time.min, tzinfo=pytz.UTC)
        days = self.request.query_params.get("days")
        days = int(days) if days else None

        return Response(schedule.quality_report(datetime_start, days))

    @action(detail=False, methods=["get"])
    def type_options(self, request):
        # TODO: check if it needed
        choices = []
        for item in OnCallSchedule.SCHEDULE_CHOICES:
            choices.append({"value": str(item[0]), "display_name": item[1]})
        return Response(choices)

    @action(detail=True, methods=["post"])
    def reload_ical(self, request, pk):
        schedule = self.get_object()
        schedule.drop_cached_ical()
        schedule.check_empty_shifts_for_next_week()
        schedule.check_gaps_for_next_week()

        if schedule.user_group is not None:
            update_slack_user_group_for_schedules.apply_async((schedule.user_group.pk,))

        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=["get", "post", "delete"])
    def export_token(self, request, pk):
        schedule = self.get_object()

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

    @action(methods=["get"], detail=False)
    def filters(self, request):
        filter_name = request.query_params.get("search", None)
        api_root = "/api/internal/v1/"

        filter_options = [
            {
                "name": "team",
                "type": "team_select",
                "href": api_root + "teams/",
                "global": True,
            },
            {
                "name": "mine",
                "type": "boolean",
                "display_name": "Mine",
                "default": "true",
            },
            {
                "name": "used",
                "type": "boolean",
                "display_name": "Used in escalations",
                "default": "false",
            },
            {
                "name": "type",
                "type": "options",
                "options": [
                    {"display_name": "API", "value": 0},
                    {"display_name": "Ical", "value": 1},
                    {"display_name": "Web", "value": 2},
                ],
            },
        ]

        if filter_name is not None:
            filter_options = list(filter(lambda f: filter_name in f["name"], filter_options))

        return Response(filter_options)
