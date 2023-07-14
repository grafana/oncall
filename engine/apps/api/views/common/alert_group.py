from django.db.models import Q
from django_filters import rest_framework as filters
from django_filters.widgets import RangeWidget

from apps.alerts.models import AlertGroup, AlertReceiveChannel, EscalationChain
from apps.base.models.user_notification_policy_log_record import UserNotificationPolicyLogRecord
from apps.user_management.models import User
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.filters import (
    ByTeamModelFieldFilterMixin,
    DateRangeFilterMixin,
    ModelFieldFilterMixin,
    TeamModelMultipleChoiceFilter,
)

STATS_MAX_COUNT = 100001


def get_integration_queryset(request):
    if request is None:
        return AlertReceiveChannel.objects.none()

    return AlertReceiveChannel.objects_with_maintenance.filter(organization=request.user.organization)


def get_escalation_chain_queryset(request):
    if request is None:
        return EscalationChain.objects.none()

    return EscalationChain.objects.filter(organization=request.user.organization)


def get_user_queryset(request):
    if request is None:
        return User.objects.none()

    return User.objects.filter(organization=request.user.organization).distinct()


class AlertGroupFilterBackend(filters.DjangoFilterBackend):
    """
    See here for more context on how this works

    https://github.com/carltongibson/django-filter/discussions/1572
    https://youtu.be/e52S1SjuUeM?t=841
    """

    def get_filterset(self, request, queryset, view):
        filterset = super().get_filterset(request, queryset, view)

        filterset.form.fields["integration"].queryset = get_integration_queryset(request)
        filterset.form.fields["escalation_chain"].queryset = get_escalation_chain_queryset(request)

        user_queryset = get_user_queryset(request)

        filterset.form.fields["silenced_by"].queryset = user_queryset
        filterset.form.fields["acknowledged_by"].queryset = user_queryset
        filterset.form.fields["resolved_by"].queryset = user_queryset
        filterset.form.fields["invitees_are"].queryset = user_queryset
        filterset.form.fields["involved_users_are"].queryset = user_queryset

        return filterset


class AlertGroupFilter(DateRangeFilterMixin, ByTeamModelFieldFilterMixin, ModelFieldFilterMixin, filters.FilterSet):
    """
    Examples of possible date formats here https://docs.djangoproject.com/en/1.9/ref/settings/#datetime-input-formats
    """

    FILTER_BY_INVOLVED_USERS_ALERT_GROUPS_CUTOFF = 1000

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
        queryset=None,
        to_field_name="public_primary_key",
        method=ModelFieldFilterMixin.filter_model_field.__name__,
    )
    integration = filters.ModelMultipleChoiceFilter(
        field_name="channel",
        queryset=None,
        to_field_name="public_primary_key",
        method=ModelFieldFilterMixin.filter_model_field.__name__,
    )
    escalation_chain = filters.ModelMultipleChoiceFilter(
        field_name="channel_filter__escalation_chain",
        queryset=None,
        to_field_name="public_primary_key",
        method=ModelFieldFilterMixin.filter_model_field.__name__,
    )
    started_at_range = filters.DateFromToRangeFilter(
        field_name="started_at", widget=RangeWidget(attrs={"type": "date"})
    )
    resolved_by = filters.ModelMultipleChoiceFilter(
        field_name="resolved_by_user",
        queryset=None,
        to_field_name="public_primary_key",
        method=ModelFieldFilterMixin.filter_model_field.__name__,
    )
    acknowledged_by = filters.ModelMultipleChoiceFilter(
        field_name="acknowledged_by_user",
        queryset=None,
        to_field_name="public_primary_key",
        method=ModelFieldFilterMixin.filter_model_field.__name__,
    )
    invitees_are = filters.ModelMultipleChoiceFilter(
        queryset=None, to_field_name="public_primary_key", method="filter_invitees_are"
    )
    involved_users_are = filters.ModelMultipleChoiceFilter(
        queryset=None, to_field_name="public_primary_key", method="filter_by_involved_users"
    )
    with_resolution_note = filters.BooleanFilter(method="filter_with_resolution_note")
    mine = filters.BooleanFilter(method="filter_mine")
    team = TeamModelMultipleChoiceFilter(field_name="channel__team")

    class Meta:
        model = AlertGroup
        fields = [
            "id__in",
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
            filters["new"] = AlertGroup.get_new_state_filter()
        if AlertGroup.SILENCED in statuses:
            filters["silenced"] = AlertGroup.get_silenced_state_filter()
        if AlertGroup.ACKNOWLEDGED in statuses:
            filters["acknowledged"] = AlertGroup.get_acknowledged_state_filter()
        if AlertGroup.RESOLVED in statuses:
            filters["resolved"] = AlertGroup.get_resolved_state_filter()

        for item in filters:
            q_objects |= filters[item]

        queryset = queryset.filter(q_objects)

        return queryset

    def filter_invitees_are(self, queryset, name, value):
        users = value

        if not users:
            return queryset

        queryset = queryset.filter(log_records__author__in=users).distinct()

        return queryset

    def filter_by_involved_users(self, queryset, name, value):
        users = value

        if not users:
            return queryset

        # This is expensive to filter all alert groups with involved users,
        # so we limit the number of alert groups to filter by the last 1000 for the given user(s)
        alert_group_notified_users_ids = list(
            UserNotificationPolicyLogRecord.objects.filter(author__in=users)
            .order_by("-alert_group_id")
            .values_list("alert_group_id", flat=True)
            .distinct()[: self.FILTER_BY_INVOLVED_USERS_ALERT_GROUPS_CUTOFF]
        )

        queryset = queryset.filter(
            # user was notified
            Q(id__in=alert_group_notified_users_ids)
            |
            # or interacted with the alert group
            Q(acknowledged_by_user__in=users)
            | Q(resolved_by_user__in=users)
            | Q(silenced_by_user__in=users)
        ).distinct()
        return queryset

    def filter_mine(self, queryset, name, value):
        if value:
            return self.filter_by_involved_users(queryset, "users", [self.request.user])
        return queryset

    def filter_with_resolution_note(self, queryset, name, value):
        if value is True:
            queryset = queryset.filter(Q(resolution_notes__isnull=False, resolution_notes__deleted_at=None)).distinct()
        elif value is False:
            queryset = queryset.filter(
                Q(resolution_notes__isnull=True) | ~Q(resolution_notes__deleted_at=None)
            ).distinct()
        return queryset
