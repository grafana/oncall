import typing

from django.core.paginator import EmptyPage
from rest_framework.pagination import BasePagination, CursorPagination, PageNumberPagination
from rest_framework.response import Response

from common.api_helpers.utils import create_engine_url

PaginatedData = typing.List[typing.Any]


class BasePaginatedResponseData(typing.TypedDict):
    next: str | None
    previous: str | None
    results: PaginatedData
    page_size: int


class PageBasedPaginationResponseData(BasePaginatedResponseData):
    count: int
    current_page_number: int
    total_pages: int


class BasePathPrefixedPagination(BasePagination):
    max_page_size = 100
    page_query_param = "page"
    page_size_query_param = "perpage"

    def paginate_queryset(self, queryset, request, view=None):
        request.build_absolute_uri = lambda: create_engine_url(request.get_full_path())
        return super().paginate_queryset(queryset, request, view)


class PathPrefixedPagePagination(BasePathPrefixedPagination, PageNumberPagination):
    def get_paginated_response(self, data: PaginatedData) -> Response:
        response = super().get_paginated_response(data)
        response.data.update(
            {
                "page_size": self.get_page_size(self.request),
                "current_page_number": self.page.number,
                "total_pages": self.page.paginator.num_pages,
            }
        )
        return response

    def get_paginated_response_schema(self, schema):
        paginated_schema = super().get_paginated_response_schema(schema)
        paginated_schema["properties"].update(
            {
                "page_size": {"type": "integer"},
                "current_page_number": {"type": "integer"},
                "total_pages": {"type": "integer"},
            }
        )
        return paginated_schema

    def paginate_queryset(self, queryset, request, view=None):
        request.build_absolute_uri = lambda: create_engine_url(request.get_full_path())
        per_page = request.query_params.get(self.page_size_query_param, self.page_size)
        try:
            per_page = int(per_page)
        except ValueError:
            per_page = self.page_size

        if per_page < 1:
            per_page = self.page_size

        paginator = self.django_paginator_class(queryset, per_page)
        page_number = request.query_params.get(self.page_query_param, 1)
        try:
            page_number = int(page_number)
        except ValueError:
            page_number = 1

        if page_number < 1:
            page_number = 1

        try:
            self.page = self.get_page(page_number, paginator)
        except EmptyPage:
            self.page = paginator.page(paginator.num_pages)

        if paginator.num_pages > 1 and self.template is not None:
            self.display_page_controls = True

        self.request = request
        return list(self.page)

    def get_page(self, page_number, paginator):
        try:
            return paginator.page(page_number)
        except EmptyPage:
            return paginator.page(paginator.num_pages)


class PathPrefixedCursorPagination(BasePathPrefixedPagination, CursorPagination):
    def get_paginated_response(self, data: PaginatedData) -> Response:
        response = super().get_paginated_response(data)
        response.data.update({"page_size": self.page_size})
        return response

    def get_paginated_response_schema(self, schema):
        paginated_schema = super().get_paginated_response_schema(schema)
        paginated_schema["properties"].update({"page_size": {"type": "integer"}})
        return paginated_schema


class HundredPageSizePaginator(PathPrefixedPagePagination):
    page_size = 100


class FiftyPageSizePaginator(PathPrefixedPagePagination):
    page_size = 50


class TwentyFivePageSizePaginator(PathPrefixedPagePagination):
    page_size = 25


class FifteenPageSizePaginator(PathPrefixedPagePagination):
    page_size = 15


class AlertGroupCursorPaginator(PathPrefixedCursorPagination):
    page_size = 25
    ordering = "-started_at"
