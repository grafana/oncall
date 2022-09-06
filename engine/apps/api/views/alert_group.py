from datetime import timedelta

from django.db.models import Count, Max, Q
from django.utils import timezone
from django_filters import rest_framework as filters
from django_filters.widgets import RangeWidget
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.alerts.constants import ActionSource
from apps.alerts.models import Alert, AlertGroup, AlertReceiveChannel
from apps.api.permissions import MODIFY_ACTIONS, READ_ACTIONS, ActionPermission, AnyRole, IsAdminOrEditor
from apps.api.serializers.alert_group import AlertGroupListSerializer, AlertGroupSerializer
from apps.auth_token.auth import MobileAppAuthTokenAuthentication, PluginAuthentication
from apps.user_management.models import User
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.filters import DateRangeFilterMixin, ModelFieldFilterMixin
from common.api_helpers.mixins import PreviewTemplateMixin, PublicPrimaryKeyMixin, TeamFilteringMixin
from common.api_helpers.paginators import TwentyFiveCursorPaginator


def get_integration_queryset(request):
    if request is None:
        return AlertReceiveChannel.objects.none()

    return AlertReceiveChannel.objects_with_maintenance.filter(organization=request.user.organization)


def get_user_queryset(request):
    if request is None:
        return User.objects.none()

    return User.objects.filter(organization=request.user.organization).distinct()


class AlertGroupFilter(DateRangeFilterMixin, ModelFieldFilterMixin, filters.FilterSet):
    """
    Examples of possible date formats here https://docs.djangoproject.com/en/1.9/ref/settings/#datetime-input-formats
    """

    started_at_gte = filters.DateTimeFilter(field_name="started_at", lookup_expr="gte")
    started_at_lte = filters.DateTimeFilter(field_name="started_at", lookup_expr="lte")
    resolved_at_lte = filters.DateTimeFilter(field_name="resolved_at", lookup_expr="lte")
    is_root = filters.BooleanFilter(field_name="root_alert_group", lookup_expr="isnull")
    id__in = filters.BaseInFilter(field_name="public_primary_key", lookup_expr="in")
    status = filters.MultipleChoiceFilter(choices=AlertGroup.STATUS_CHOICES, method="filter_status")
    started_at = filters.CharFilter(field_name="started_at", method=DateRangeFilterMixin.filter_date_range.__name__)
    resolved_at = filters.CharFilter(field_name="resolved_at", method=DateRangeFilterMixin.filter_date_range.__name__)
    silenced_at = filters.CharFilter(field_name="silenced_at", method=DateRangeFilterMixin.filter_date_range.__name__)
    silenced_by = filters.ModelMultipleChoiceFilter(
        field_name="silenced_by_user",
        queryset=get_user_queryset,
        to_field_name="public_primary_key",
        method=ModelFieldFilterMixin.filter_model_field.__name__,
    )
    integration = filters.ModelMultipleChoiceFilter(
        field_name="channel_filter__alert_receive_channel",
        queryset=get_integration_queryset,
        to_field_name="public_primary_key",
        method=ModelFieldFilterMixin.filter_model_field.__name__,
    )
    started_at_range = filters.DateFromToRangeFilter(
        field_name="started_at", widget=RangeWidget(attrs={"type": "date"})
    )
    resolved_by = filters.ModelMultipleChoiceFilter(
        field_name="resolved_by_user",
        queryset=get_user_queryset,
        to_field_name="public_primary_key",
        method=ModelFieldFilterMixin.filter_model_field.__name__,
    )
    acknowledged_by = filters.ModelMultipleChoiceFilter(
        field_name="acknowledged_by_user",
        queryset=get_user_queryset,
        to_field_name="public_primary_key",
        method=ModelFieldFilterMixin.filter_model_field.__name__,
    )
    invitees_are = filters.ModelMultipleChoiceFilter(
        queryset=get_user_queryset, to_field_name="public_primary_key", method="filter_invitees_are"
    )
    with_resolution_note = filters.BooleanFilter(method="filter_with_resolution_note")

    class Meta:
        model = AlertGroup
        fields = [
            "id__in",
            "resolved",
            "acknowledged",
            "started_at_gte",
            "started_at_lte",
            "resolved_at_lte",
            "is_root",
            "resolved_by",
            "acknowledged_by",
        ]

    def filter_status(self, queryset, name, value):
        if not value:
            return queryset
        try:
            statuses = list(map(int, value))
        except ValueError:
            raise BadRequest(detail="Invalid status value")

        filters = {}
        q_objects = Q()

        if AlertGroup.NEW in statuses:
            filters["new"] = Q(silenced=False) & Q(acknowledged=False) & Q(resolved=False)
        if AlertGroup.SILENCED in statuses:
            filters["silenced"] = Q(silenced=True) & Q(acknowledged=False) & Q(resolved=False)
        if AlertGroup.ACKNOWLEDGED in statuses:
            filters["acknowledged"] = Q(acknowledged=True) & Q(resolved=False)
        if AlertGroup.RESOLVED in statuses:
            filters["resolved"] = Q(resolved=True)

        for item in filters:
            q_objects |= filters[item]

        queryset = queryset.filter(q_objects)

        return queryset

    def filter_invitees_are(self, queryset, name, value):
        users = value

        if not users:
            return queryset

        queryset = queryset.filter(acknowledged=False, resolved=False, log_records__author__in=users).distinct()

        return queryset

    def filter_with_resolution_note(self, queryset, name, value):
        if value is True:
            queryset = queryset.filter(Q(resolution_notes__isnull=False, resolution_notes__deleted_at=None)).distinct()
        elif value is False:
            queryset = queryset.filter(
                Q(resolution_notes__isnull=True) | ~Q(resolution_notes__deleted_at=None)
            ).distinct()
        return queryset


class AlertGroupTeamFilteringMixin(TeamFilteringMixin):
    TEAM_LOOKUP = "channel__team"


class AlertGroupView(
    PreviewTemplateMixin,
    AlertGroupTeamFilteringMixin,
    PublicPrimaryKeyMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    authentication_classes = (
        MobileAppAuthTokenAuthentication,
        PluginAuthentication,
    )
    permission_classes = (IsAuthenticated, ActionPermission)

    action_permissions = {
        IsAdminOrEditor: (
            *MODIFY_ACTIONS,
            "acknowledge",
            "unacknowledge",
            "resolve",
            "unresolve",
            "attach",
            "unattach",
            "silence",
            "unsilence",
            "bulk_action",
            "preview_template",
        ),
        AnyRole: (
            *READ_ACTIONS,
            "stats",
            "filters",
            "silence_options",
            "bulk_action_options",
        ),
    }

    http_method_names = ["get", "post"]

    serializer_class = AlertGroupSerializer

    pagination_class = TwentyFiveCursorPaginator

    filter_backends = [SearchFilter, filters.DjangoFilterBackend]
    search_fields = ["public_primary_key", "inside_organization_number", "web_title_cache"]

    filterset_class = AlertGroupFilter

    def get_serializer_class(self):
        if self.action == "list":
            return AlertGroupListSerializer

        return super().get_serializer_class()

    def get_queryset(self):
        # no select_related or prefetch_related is used at this point, it will be done on paginate_queryset.
        queryset = AlertGroup.unarchived_objects.filter(
            channel__organization=self.request.auth.organization, channel__team=self.request.user.current_team
        ).only("id")

        return queryset

    def paginate_queryset(self, queryset):
        """
        All SQL joins (select_related and prefetch_related) will be performed AFTER pagination, so it only joins tables
        for 25 alert groups, not the whole table.
        """
        alert_groups = super().paginate_queryset(queryset)
        alert_groups = self.enrich(alert_groups)
        return alert_groups

    def get_object(self):
        obj = super().get_object()
        obj = self.enrich([obj])[0]
        return obj

    def enrich(self, alert_groups):
        """
        This method performs select_related and prefetch_related (using setup_eager_loading) as well as in-memory joins
        to add additional info like alert_count and last_alert for every alert group efficiently.
        We need the last_alert because it's used by AlertGroupWebRenderer.
        """

        # enrich alert groups with select_related and prefetch_related
        alert_group_pks = [alert_group.pk for alert_group in alert_groups]
        queryset = AlertGroup.all_objects.filter(pk__in=alert_group_pks).order_by("-pk")

        # do not load cached_render_for_web as it's deprecated and can be very large
        queryset = queryset.defer("cached_render_for_web")

        queryset = self.get_serializer_class().setup_eager_loading(queryset)
        alert_groups = list(queryset)

        # get info on alerts count and last alert ID for every alert group
        alerts_info = (
            Alert.objects.values("group_id")
            .filter(group_id__in=alert_group_pks)
            .annotate(alerts_count=Count("group_id"), last_alert_id=Max("id"))
        )
        alerts_info_map = {info["group_id"]: info for info in alerts_info}

        # fetch last alerts for every alert group
        last_alert_ids = [info["last_alert_id"] for info in alerts_info_map.values()]
        last_alerts = Alert.objects.filter(pk__in=last_alert_ids)
        for alert in last_alerts:
            # link group back to alert
            alert.group = [alert_group for alert_group in alert_groups if alert_group.pk == alert.group_id][0]
            alerts_info_map[alert.group_id].update({"last_alert": alert})

        # add additional "alerts_count" and "last_alert" fields to every alert group
        for alert_group in alert_groups:
            try:
                alert_group.last_alert = alerts_info_map[alert_group.pk]["last_alert"]
                alert_group.alerts_count = alerts_info_map[alert_group.pk]["alerts_count"]
            except KeyError:
                # alert group has no alerts
                alert_group.last_alert = None
                alert_group.alerts_count = 0

        return alert_groups

    @action(detail=False)
    def stats(self, *args, **kwargs):
        alert_groups = self.filter_queryset(self.get_queryset())
        # Only count field is used, other fields left just in case for the backward compatibility
        return Response(
            {
                "count": alert_groups.filter().count(),
                "count_previous_same_period": 0,
                "alert_group_rate_to_previous_same_period": 1,
                "count_escalations": 0,
                "count_escalations_previous_same_period": 0,
                "escalation_rate_to_previous_same_period": 1,
                "average_response_time": None,
                "average_response_time_to_previous_same_period": None,
                "average_response_time_rate_to_previous_same_period": 0,
                "prev_period_in_days": 1,
            }
        )

    @action(methods=["post"], detail=True)
    def acknowledge(self, request, pk):
        alert_group = self.get_object()
        if alert_group.is_maintenance_incident:
            raise BadRequest(detail="Can't acknowledge maintenance alert group")
        if alert_group.root_alert_group is not None:
            raise BadRequest(detail="Can't acknowledge an attached alert group")
        alert_group.acknowledge_by_user(self.request.user, action_source=ActionSource.WEB)

        return Response(AlertGroupSerializer(alert_group, context={"request": self.request}).data)

    @action(methods=["post"], detail=True)
    def unacknowledge(self, request, pk):
        alert_group = self.get_object()
        if alert_group.is_maintenance_incident:
            raise BadRequest(detail="Can't unacknowledge maintenance alert group")

        if alert_group.root_alert_group is not None:
            raise BadRequest(detail="Can't unacknowledge an attached alert group")

        if not alert_group.acknowledged:
            raise BadRequest(detail="The alert group is not acknowledged")

        if alert_group.resolved:
            raise BadRequest(detail="Can't unacknowledge a resolved alert group")

        alert_group.un_acknowledge_by_user(self.request.user, action_source=ActionSource.WEB)

        return Response(AlertGroupSerializer(alert_group, context={"request": self.request}).data)

    @action(methods=["post"], detail=True)
    def resolve(self, request, pk):
        alert_group = self.get_object()
        organization = self.request.user.organization

        if alert_group.root_alert_group is not None:
            raise BadRequest(detail="Can't resolve an attached alert group")

        if alert_group.is_maintenance_incident:
            alert_group.stop_maintenance(self.request.user)
        else:
            if organization.is_resolution_note_required and not alert_group.has_resolution_notes:
                return Response(
                    data="Alert group without resolution note cannot be resolved due to organization settings.",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            alert_group.resolve_by_user(self.request.user, action_source=ActionSource.WEB)
        return Response(AlertGroupSerializer(alert_group, context={"request": self.request}).data)

    @action(methods=["post"], detail=True)
    def unresolve(self, request, pk):
        alert_group = self.get_object()
        if alert_group.is_maintenance_incident:
            raise BadRequest(detail="Can't unresolve maintenance alert group")

        if alert_group.root_alert_group is not None:
            raise BadRequest(detail="Can't unresolve an attached alert group")

        if not alert_group.resolved:
            raise BadRequest(detail="The alert group is not resolved")

        alert_group.un_resolve_by_user(self.request.user, action_source=ActionSource.WEB)
        return Response(AlertGroupSerializer(alert_group, context={"request": self.request}).data)

    @action(methods=["post"], detail=True)
    def attach(self, request, pk=None):
        alert_group = self.get_object()
        if alert_group.is_maintenance_incident:
            raise BadRequest(detail="Can't attach maintenance alert group")
        if alert_group.dependent_alert_groups.count() > 0:
            raise BadRequest(detail="Can't attach an alert group because it has another alert groups attached to it")
        if not alert_group.is_root_alert_group:
            raise BadRequest(detail="Can't attach an alert group because it has already been attached")

        try:
            root_alert_group = self.get_queryset().get(public_primary_key=request.data["root_alert_group_pk"])
        except AlertGroup.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if root_alert_group.resolved or root_alert_group.root_alert_group is not None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if root_alert_group == alert_group:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        alert_group.attach_by_user(self.request.user, root_alert_group, action_source=ActionSource.WEB)
        return Response(AlertGroupSerializer(alert_group, context={"request": self.request}).data)

    @action(methods=["post"], detail=True)
    def unattach(self, request, pk=None):
        alert_group = self.get_object()
        if alert_group.is_maintenance_incident:
            raise BadRequest(detail="Can't unattach maintenance alert group")
        if alert_group.is_root_alert_group:
            raise BadRequest(detail="Can't unattach an alert group because it is not attached")

        alert_group.un_attach_by_user(self.request.user, action_source=ActionSource.WEB)
        return Response(AlertGroupSerializer(alert_group, context={"request": self.request}).data)

    @action(methods=["post"], detail=True)
    def silence(self, request, pk=None):
        alert_group = self.get_object()

        delay = request.data.get("delay")
        if delay is None:
            raise BadRequest(detail="Please specify a delay for silence")

        if alert_group.root_alert_group is not None:
            raise BadRequest(detail="Can't silence an attached alert group")

        alert_group.silence_by_user(request.user, silence_delay=delay, action_source=ActionSource.WEB)
        return Response(AlertGroupSerializer(alert_group, context={"request": request}).data)

    @action(methods=["get"], detail=False)
    def silence_options(self, request):
        data = [
            {"value": value, "display_name": display_name} for value, display_name in AlertGroup.SILENCE_DELAY_OPTIONS
        ]
        return Response(data)

    @action(methods=["post"], detail=True)
    def unsilence(self, request, pk=None):
        alert_group = self.get_object()

        if not alert_group.silenced:
            raise BadRequest(detail="The alert group is not silenced")

        if alert_group.resolved:
            raise BadRequest(detail="Can't unsilence a resolved alert group")

        if alert_group.acknowledged:
            raise BadRequest(detail="Can't unsilence an acknowledged alert group")

        if alert_group.root_alert_group is not None:
            raise BadRequest(detail="Can't unsilence an attached alert group")

        alert_group.un_silence_by_user(request.user, action_source=ActionSource.WEB)

        return Response(AlertGroupSerializer(alert_group, context={"request": request}).data)

    @action(methods=["get"], detail=False)
    def filters(self, request):
        filter_name = request.query_params.get("search", None)
        api_root = "/api/internal/v1/"

        now = timezone.now()
        week_ago = now - timedelta(days=7)

        default_datetime_range = "{}/{}".format(
            week_ago.strftime(DateRangeFilterMixin.DATE_FORMAT),
            now.strftime(DateRangeFilterMixin.DATE_FORMAT),
        )

        filter_options = [
            {"name": "search", "type": "search"},
            {"name": "integration", "type": "options", "href": api_root + "alert_receive_channels/?filters=true"},
            {
                "name": "acknowledged_by",
                "type": "options",
                "href": api_root + "users/?filters=true&roles=0&roles=1&roles=2",
                "default": {"display_name": self.request.user.username, "value": self.request.user.public_primary_key},
            },
            {
                "name": "resolved_by",
                "type": "options",
                "href": api_root + "users/?filters=true&roles=0&roles=1&roles=2",
            },
            {
                "name": "silenced_by",
                "type": "options",
                "href": api_root + "users/?filters=true&roles=0&roles=1&roles=2",
            },
            {
                "name": "invitees_are",
                "type": "options",
                "href": api_root + "users/?filters=true&roles=0&roles=1&roles=2",
            },
            {
                "name": "status",
                "type": "options",
                "options": [
                    {"display_name": "new", "value": AlertGroup.NEW},
                    {"display_name": "acknowledged", "value": AlertGroup.ACKNOWLEDGED},
                    {"display_name": "resolved", "value": AlertGroup.RESOLVED},
                    {"display_name": "silenced", "value": AlertGroup.SILENCED},
                ],
            },
            # {'name': 'is_root', 'type': 'boolean', 'default': True},
            {
                "name": "started_at",
                "type": "daterange",
                "default": default_datetime_range,
            },
            {
                "name": "resolved_at",
                "type": "daterange",
                "default": default_datetime_range,
            },
            {
                "name": "with_resolution_note",
                "type": "boolean",
                "default": "true",
            },
        ]

        if filter_name is not None:
            filter_options = list(filter(lambda f: filter_name in f["name"], filter_options))

        return Response(filter_options)

    @action(methods=["post"], detail=False)
    def bulk_action(self, request):
        alert_group_public_pks = self.request.data.get("alert_group_pks", [])
        action_with_incidents = self.request.data.get("action", None)
        delay = self.request.data.get("delay")
        kwargs = {}

        if action_with_incidents not in AlertGroup.BULK_ACTIONS:
            return Response("Unknown action", status=status.HTTP_400_BAD_REQUEST)

        if action_with_incidents == AlertGroup.SILENCE:
            if delay is None:
                raise BadRequest(detail="Please specify a delay for silence")
            kwargs["silence_delay"] = delay

        alert_groups = AlertGroup.unarchived_objects.filter(
            channel__organization=self.request.auth.organization, public_primary_key__in=alert_group_public_pks
        )

        kwargs["user"] = self.request.user
        kwargs["alert_groups"] = alert_groups

        method = getattr(AlertGroup, f"bulk_{action_with_incidents}")
        method(**kwargs)

        return Response(status=status.HTTP_200_OK)

    @action(methods=["get"], detail=False)
    def bulk_action_options(self, request):
        return Response(
            [{"value": action_name, "display_name": action_name} for action_name in AlertGroup.BULK_ACTIONS]
        )

    # This method is required for PreviewTemplateMixin
    def get_alert_to_template(self):
        return self.get_object().alerts.first()
