from datetime import datetime, timedelta

from django import forms
from django.db import models
from django.db.models import CharField, Q
from django.db.models.constants import LOOKUP_SEP
from django.db.models.functions import Cast
from django.utils import timezone
from django_filters import rest_framework as filters
from django_filters.widgets import RangeWidget
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.alerts.constants import ActionSource
from apps.alerts.models import AlertGroup, AlertReceiveChannel
from apps.alerts.tasks import invalidate_web_cache_for_alert_group
from apps.api.permissions import MODIFY_ACTIONS, READ_ACTIONS, ActionPermission, AnyRole, IsAdminOrEditor
from apps.api.serializers.alert_group import AlertGroupSerializer
from apps.auth_token.auth import MobileAppAuthTokenAuthentication, PluginAuthentication
from apps.user_management.models import User
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.filters import DateRangeFilterMixin, ModelFieldFilterMixin
from common.api_helpers.mixins import PreviewTemplateMixin, PublicPrimaryKeyMixin
from common.api_helpers.paginators import FiftyPageSizePaginator


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


class CustomSearchFilter(SearchFilter):
    def must_call_distinct(self, queryset, search_fields):
        """
        Return True if 'distinct()' should be used to query the given lookups.
        """
        for search_field in search_fields:
            opts = queryset.model._meta
            if search_field[0] in self.lookup_prefixes:
                search_field = search_field[1:]

            # From https://github.com/encode/django-rest-framework/pull/6240/files#diff-01f357e474dd8fd702e4951b9227bffcR88
            # Annotated fields do not need to be distinct
            if isinstance(queryset, models.QuerySet) and search_field in queryset.query.annotations:
                continue

            parts = search_field.split(LOOKUP_SEP)
            for part in parts:
                field = opts.get_field(part)
                if hasattr(field, "get_path_info"):
                    # This field is a relation, update opts to follow the relation
                    path_info = field.get_path_info()
                    opts = path_info[-1].to_opts
                    if any(path.m2m for path in path_info):
                        # This field is a m2m relation so we know we need to call distinct
                        return True
        return False


class AlertGroupView(
    PreviewTemplateMixin,
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

    pagination_class = FiftyPageSizePaginator

    filter_backends = [CustomSearchFilter, filters.DjangoFilterBackend]
    search_fields = ["cached_render_for_web_str"]

    filterset_class = AlertGroupFilter

    def list(self, request, *args, **kwargs):
        """
        It's compute-heavy so we rely on cache here.
        Attention: Make sure to invalidate cache if you update the format!
        """
        queryset = self.filter_queryset(self.get_queryset(eager=False, readonly=True))

        page = self.paginate_queryset(queryset)
        skip_slow_rendering = request.query_params.get("skip_slow_rendering") == "true"
        data = []

        for alert_group in page:
            if alert_group.cached_render_for_web == {}:
                # We cannot give empty data to web. So caching synchronously here.
                if skip_slow_rendering:
                    # We just return dummy data.
                    # Cache is not launched because after skip_slow_rendering request should come usual one
                    # which will start caching
                    data.append({"pk": alert_group.pk, "short": True})
                else:
                    # Synchronously cache and return. It could be slow.
                    alert_group.cache_for_web(alert_group.channel.organization)
                    data.append(alert_group.cached_render_for_web)
            else:
                data.append(alert_group.cached_render_for_web)
                if not skip_slow_rendering:
                    # Cache is not launched because after skip_slow_rendering request should come usual one
                    # which will start caching
                    alert_group.schedule_cache_for_web()

        return self.get_paginated_response(data)

    def get_queryset(self, eager=True, readonly=False, order=True):
        if readonly:
            queryset = AlertGroup.unarchived_objects.using_readonly_db
        else:
            queryset = AlertGroup.unarchived_objects

        queryset = queryset.filter(
            channel__organization=self.request.auth.organization,
            channel__team=self.request.user.current_team,
        )

        if order:
            queryset = queryset.order_by("-started_at")

        queryset = queryset.annotate(cached_render_for_web_str=Cast("cached_render_for_web", output_field=CharField()))

        if eager:
            queryset = self.serializer_class.setup_eager_loading(queryset)
        return queryset

    def get_alert_groups_and_days_for_previous_same_period(self):
        prev_alert_groups = AlertGroup.unarchived_objects.none()
        delta_days = None

        started_at = self.request.query_params.get("started_at", None)
        if started_at is not None:
            started_at_gte, started_at_lte = AlertGroupFilter.parse_custom_datetime_range(started_at)
            delta_days = None
            if started_at_lte is not None:
                started_at_lte = forms.DateTimeField().to_python(started_at_lte)
            else:
                started_at_lte = datetime.now()

            if started_at_gte is not None:
                started_at_gte = forms.DateTimeField().to_python(value=started_at_gte)
                delta = started_at_lte.replace(tzinfo=None) - started_at_gte.replace(tzinfo=None)
                prev_alert_groups = self.get_queryset().filter(
                    started_at__range=[started_at_gte - delta, started_at_gte]
                )
                delta_days = delta.days
        return prev_alert_groups, delta_days

    @action(detail=False)
    def stats(self, *args, **kwargs):
        alert_groups = self.filter_queryset(self.get_queryset(eager=False))
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
        invalidate_web_cache_for_alert_group(alert_group_pk=alert_group.pk)

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
        invalidate_web_cache_for_alert_group(alert_group_pk=alert_group.pk)

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
        invalidate_web_cache_for_alert_group(alert_group_pk=alert_group.pk)
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
        invalidate_web_cache_for_alert_group(alert_group_pk=alert_group.pk)
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
        invalidate_web_cache_for_alert_group(alert_group_pk=alert_group.pk)
        invalidate_web_cache_for_alert_group(alert_group_pk=root_alert_group.pk)
        return Response(AlertGroupSerializer(alert_group, context={"request": self.request}).data)

    @action(methods=["post"], detail=True)
    def unattach(self, request, pk=None):
        alert_group = self.get_object()
        if alert_group.is_maintenance_incident:
            raise BadRequest(detail="Can't unattach maintenance alert group")
        if alert_group.is_root_alert_group:
            raise BadRequest(detail="Can't unattach an alert group because it is not attached")
        root_alert_group_pk = alert_group.root_alert_group_id
        alert_group.un_attach_by_user(self.request.user, action_source=ActionSource.WEB)
        invalidate_web_cache_for_alert_group(alert_group_pk=alert_group.pk)
        invalidate_web_cache_for_alert_group(alert_group_pk=root_alert_group_pk)
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
        invalidate_web_cache_for_alert_group(alert_group_pk=alert_group.pk)
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

        alert_groups = self.get_queryset(eager=False).filter(public_primary_key__in=alert_group_public_pks)
        alert_group_pks = list(alert_groups.values_list("id", flat=True))
        invalidate_web_cache_for_alert_group(alert_group_pks=alert_group_pks)

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
