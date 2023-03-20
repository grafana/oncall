from datetime import datetime

from django.db.models import Q
from django_filters import rest_framework as filters
from django_filters.utils import handle_timezone

from apps.user_management.models import Team
from common.api_helpers.exceptions import BadRequest


class DateRangeFilterMixin:
    DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"

    def filter_date_range(self, queryset, name, value):
        start_time, end_time = self.parse_custom_datetime_range(value)

        filter_kwargs = {}
        if start_time:
            filter_kwargs[f"{name}__gte"] = start_time
        if end_time:
            filter_kwargs[f"{name}__lte"] = end_time
        return queryset.filter(**filter_kwargs)

    @classmethod
    def parse_custom_datetime_range(cls, value):
        if not value:
            return None, None

        date_entries = value.split("/")

        if len(date_entries) != 2:
            raise BadRequest(detail="Invalid range value")

        try:
            start_date = datetime.strptime(date_entries[0], cls.DATE_FORMAT)
            end_date = datetime.strptime(date_entries[1], cls.DATE_FORMAT)
        except ValueError:
            raise BadRequest(detail="Invalid range value")

        if start_date > end_date:
            raise BadRequest(detail="Invalid range value")

        start_date = handle_timezone(start_date, False)
        end_date = handle_timezone(end_date, False)

        return start_date, end_date


class ModelFieldFilterMixin:
    def filter_model_field(self, queryset, name, value):
        if not value:
            return queryset
        lookup_kwargs = {f"{name}__in": value}
        queryset = queryset.filter(**lookup_kwargs)
        return queryset


class ByTeamModelFieldFilterMixin:
    FILTER_FIELD_NAME = "team"

    def filter_model_field_with_single_value(self, queryset, name, value):
        if not value:
            return queryset
        # ModelChoiceFilter
        filter = self.filters[ByTeamModelFieldFilterMixin.FILTER_FIELD_NAME]
        if filter.null_value == value:
            lookup_kwargs = {f"{name}__isnull": True}
        else:
            lookup_kwargs = {f"{name}": value}
        queryset = queryset.filter(**lookup_kwargs)
        return queryset

    def filter_model_field_with_multiple_values(self, queryset, name, values):
        if not values:
            return queryset
        filter = self.filters[ByTeamModelFieldFilterMixin.FILTER_FIELD_NAME]
        null_team_lookup = None
        for value in values:
            if filter.null_value == value:
                null_team_lookup = Q(**{f"{name}__isnull": True})
                values.remove(value)
        teams_lookup = Q(**{f"{name}__in": values})
        if null_team_lookup is not None:
            teams_lookup = teams_lookup | null_team_lookup

        queryset = queryset.filter(teams_lookup)
        return queryset


def get_team_queryset(request):
    if request is None:
        return Team.objects.none()

    return request.user.organization.teams.all()


class ByTeamFilter(ByTeamModelFieldFilterMixin, filters.FilterSet):
    team_id = filters.ModelChoiceFilter(
        field_name="team",
        queryset=get_team_queryset,
        to_field_name="public_primary_key",
        null_label="noteam",
        null_value="null",
        method=ByTeamModelFieldFilterMixin.filter_model_field_with_single_value.__name__,
    )


class TeamModelMultipleChoiceFilter(filters.ModelMultipleChoiceFilter):
    def __init__(
        self,
        field_name="team",
        queryset=get_team_queryset,
        to_field_name="public_primary_key",
        null_label="noteam",
        null_value="null",
        method=ByTeamModelFieldFilterMixin.filter_model_field_with_multiple_values.__name__,
    ):
        super().__init__(
            field_name=field_name,
            queryset=queryset,
            to_field_name=to_field_name,
            null_label=null_label,
            null_value=null_value,
            method=method,
        )
