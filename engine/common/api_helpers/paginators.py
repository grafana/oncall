import typing

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
    ordering = "-started_at"  # ordering by "-started_at", so it uses the right index (see AlertGroup.Meta.indexes)
