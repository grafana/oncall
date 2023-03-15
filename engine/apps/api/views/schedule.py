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
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
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
from apps.auth_token.auth import PluginAuthentication
from apps.auth_token.constants import SCHEDULE_EXPORT_TOKEN_NAME
from apps.auth_token.models import ScheduleExportAuthToken
from apps.schedules.models import OnCallSchedule
from apps.schedules.quality_score import get_schedule_quality_score
from apps.slack.models import SlackChannel
from apps.slack.tasks import update_slack_user_group_for_schedules
from common.api_helpers.exceptions import BadRequest, Conflict
from common.api_helpers.filters import ByTeamModelFieldFilterMixin, ModelFieldFilterMixin, get_team_queryset
from common.api_helpers.mixins import (
    CreateSerializerMixin,
    PublicPrimaryKeyMixin,
    ShortSerializerMixin,
    TeamFilteringMixin,
    UpdateSerializerMixin,
)
from common.api_helpers.utils import create_engine_url, get_date_range_from_request
from common.insight_log import EntityEvent, write_resource_insight_log
from common.timezones import raise_exception_if_not_valid_timezone

EVENTS_FILTER_BY_ROTATION = "rotation"
EVENTS_FILTER_BY_OVERRIDE = "override"
EVENTS_FILTER_BY_FINAL = "final"

SCHEDULE_TYPE_TO_CLASS = {
    str(num_type): cls for cls, num_type in PolymorphicScheduleSerializer.SCHEDULE_CLASS_TO_TYPE.items()
}


class SchedulePagination(PageNumberPagination):
    page_size = 10
    page_query_param = "page"
    page_size_query_param = "perpage"
    max_page_size = 50


class ScheduleFilter(ByTeamModelFieldFilterMixin, ModelFieldFilterMixin, filters.FilterSet):
    team = filters.ModelMultipleChoiceFilter(
        field_name="team",
        queryset=get_team_queryset,
        to_field_name="public_primary_key",
        null_label="noteam",
        null_value="null",
        method=ByTeamModelFieldFilterMixin.filter_model_field_with_multiple_values.__name__,
    )


class ScheduleView(
    TeamFilteringMixin,
    PublicPrimaryKeyMixin,
    ShortSerializerMixin,
    CreateSerializerMixin,
    UpdateSerializerMixin,
    ModelViewSet,
    mixins.ListModelMixin,
):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)
    rbac_permissions = {
        "metadata": [RBACPermission.Permissions.SCHEDULES_READ],
        "list": [RBACPermission.Permissions.SCHEDULES_READ],
        "retrieve": [RBACPermission.Permissions.SCHEDULES_READ],
        "events": [RBACPermission.Permissions.SCHEDULES_READ],
        "filter_events": [RBACPermission.Permissions.SCHEDULES_READ],
        "next_shifts_per_user": [RBACPermission.Permissions.SCHEDULES_READ],
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
    pagination_class = SchedulePagination

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

    def get_queryset(self):
        is_short_request = self.request.query_params.get("short", "false") == "true"
        filter_by_type = self.request.query_params.get("type")
        used = BooleanField(allow_null=True).to_internal_value(data=self.request.query_params.get("used"))
        organization = self.request.auth.organization
        team_filtering_lookup_args = self.get_team_filtering_lookup_args()
        queryset = OnCallSchedule.objects.filter(organization=organization, *team_filtering_lookup_args,).defer(
            # avoid requesting large text fields which are not used when listing schedules
            "prev_ical_file_primary",
            "prev_ical_file_overrides",
        )
        if not is_short_request:
            queryset = self._annotate_queryset(queryset)
            queryset = self.serializer_class.setup_eager_loading(queryset)
        if filter_by_type is not None and filter_by_type in SCHEDULE_TYPE_TO_CLASS:
            queryset = queryset.filter().instance_of(SCHEDULE_TYPE_TO_CLASS[filter_by_type])
        if used is not None:
            queryset = queryset.filter(escalation_policies__isnull=not used).distinct()

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

    def get_object(self):
        # get the object from the whole organization if there is a flag `get_from_organization=true`
        # otherwise get the object from the current team
        get_from_organization = self.request.query_params.get("from_organization", "false") == "true"
        if get_from_organization:
            return self.get_object_from_organization()
        return super().get_object()

    def get_object_from_organization(self):
        # use this method to get the object from the whole organization instead of the current team
        pk = self.kwargs["pk"]
        organization = self.request.auth.organization
        team_filtering_lookup_args = self.get_team_filtering_lookup_args()
        queryset = organization.oncall_schedules.filter(
            public_primary_key=pk,
            *team_filtering_lookup_args,
        )
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
        user_tz, date = self.get_request_timezone()
        with_empty = self.request.query_params.get("with_empty", False) == "true"
        with_gap = self.request.query_params.get("with_gap", False) == "true"

        schedule = self.get_object()
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

        schedule = self.get_object()

        if filter_by is not None and filter_by != EVENTS_FILTER_BY_FINAL:
            filter_by = OnCallSchedule.PRIMARY if filter_by == EVENTS_FILTER_BY_ROTATION else OnCallSchedule.OVERRIDES
            events = schedule.filter_events(
                user_tz,
                starting_date,
                days=days,
                with_empty=True,
                with_gap=resolve_schedule,
                filter_by=filter_by,
                all_day_datetime=True,
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
        schedule = self.get_object()
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
        schedule = self.get_object()
        escalation_chains = EscalationChain.objects.filter(escalation_policies__notify_schedule=schedule).distinct()

        result = [{"name": e.name, "pk": e.public_primary_key} for e in escalation_chains]
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def quality(self, request, pk):
        schedule = self.get_object()
        user_tz, date = self.get_request_timezone()
        days = int(self.request.query_params.get("days", 90))  # todo: check if days could be calculated more precisely

        events = schedule.filter_events(user_tz, date, days=days, with_empty=True, with_gap=True)

        schedule_score = get_schedule_quality_score(events, days)
        return Response(schedule_score)

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
            # {"name": "search", "type": "search"},
            {
                "name": "team",
                "type": "team_select",
                "href": api_root + "teams/",
            },
            {
                "name": "used",
                "type": "boolean",
                "default": "false",
            },
            {
                "name": "type",
                "type": "options",
                "options": [
                    {"display_name": "API", "value": 0},
                    {"display_name": "ICal", "value": 1},
                    {"display_name": "Web", "value": 2},
                ],
            },
        ]

        if filter_name is not None:
            filter_options = list(filter(lambda f: filter_name in f["name"], filter_options))

        return Response(filter_options)
