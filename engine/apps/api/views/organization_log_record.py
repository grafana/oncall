from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.serializers.organization_log_record import OrganizationLogRecordSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.base.models import OrganizationLogRecord
from apps.user_management.models import User
from common.api_helpers.filters import DateRangeFilterMixin, ModelFieldFilterMixin
from common.api_helpers.paginators import FiftyPageSizePaginator

LABEL_CHOICES = [[label, label] for label in OrganizationLogRecord.LABELS]


def get_user_queryset(request):
    if request is None:
        return User.objects.none()

    return User.objects.filter(organization=request.user.organization).distinct()


class OrganizationLogRecordFilter(DateRangeFilterMixin, ModelFieldFilterMixin, filters.FilterSet):

    author = filters.ModelMultipleChoiceFilter(
        field_name="author",
        queryset=get_user_queryset,
        to_field_name="public_primary_key",
        method=ModelFieldFilterMixin.filter_model_field.__name__,
    )
    created_at = filters.CharFilter(field_name="created_at", method=DateRangeFilterMixin.filter_date_range.__name__)
    labels = filters.MultipleChoiceFilter(choices=LABEL_CHOICES, method="filter_labels")

    class Meta:
        model = OrganizationLogRecord
        fields = ["author", "labels", "created_at"]

    def filter_labels(self, queryset, name, value):
        if not value:
            return queryset

        q_objects = Q()
        for item in value:
            q_objects &= Q(_labels__contains=item)

        queryset = queryset.filter(q_objects)

        return queryset


class OrganizationLogRecordView(mixins.ListModelMixin, viewsets.GenericViewSet):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated,)

    serializer_class = OrganizationLogRecordSerializer

    pagination_class = FiftyPageSizePaginator

    filter_backends = (
        SearchFilter,
        DjangoFilterBackend,
    )
    search_fields = ("description",)
    filterset_class = OrganizationLogRecordFilter

    def get_queryset(self):
        queryset = OrganizationLogRecord.objects.filter(organization=self.request.auth.organization).order_by(
            "-created_at"
        )
        queryset = self.serializer_class.setup_eager_loading(queryset)
        return queryset

    @action(detail=False, methods=["get"])
    def filters(self, request):
        filter_name = request.query_params.get("filter_name", None)
        api_root = "/api/internal/v1/"

        filter_options = [
            {
                "name": "search",
                "type": "search",
            },
            {
                "name": "author",
                "type": "options",
                "href": api_root + "users/?filters=true&roles=0&roles=1&roles=2",
            },
            {
                "name": "labels",
                "type": "options",
                "options": [
                    {
                        "display_name": label,
                        "value": label,
                    }
                    for label in OrganizationLogRecord.LABELS
                ],
            },
            {
                "name": "created_at",
                "type": "daterange",
                "default": f"{timezone.datetime.now() - timedelta(days=7):%Y-%m-%d/{timezone.datetime.now():%Y-%m-%d}}",
            },
        ]

        if filter_name is not None:
            filter_options = list(filter(lambda f: f["name"].startswith(filter_name), filter_options))

        return Response(filter_options)

    @action(detail=False, methods=["get"])
    def label_options(self, request):
        return Response(
            [
                {
                    "display_name": label,
                    "value": label,
                }
                for label in OrganizationLogRecord.LABELS
            ]
        )
