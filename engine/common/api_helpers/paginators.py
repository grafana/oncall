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

        # we're setting the request object explicitly here because the way the paginate_quersey works
        # between PageNumberPagination and CursorPagination is slightly different. In the latter class,
        # it does not set self.request in the paginate_queryset method, whereas in the former it does.
        # this leads to an issue in _get_base_paginated_response_data where the self.request would not be set
        self.request = request

        return super().paginate_queryset(queryset, request, view)

    def _get_base_paginated_response_data(self, data: PaginatedData) -> BasePaginatedResponseData:
        return {
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data,
            "page_size": self.get_page_size(self.request),
        }


class PathPrefixedPagePagination(BasePathPrefixedPagination, PageNumberPagination):
    def _get_paginated_response_data(self, data: PaginatedData) -> PageBasedPaginationResponseData:
        return {
            **self._get_base_paginated_response_data(data),
            "count": self.page.paginator.count,
            "current_page_number": self.page.number,
            "total_pages": self.page.paginator.num_pages,
        }

    def get_paginated_response(self, data: PaginatedData) -> Response:
        return Response(self._get_paginated_response_data(data))


class PathPrefixedCursorPagination(BasePathPrefixedPagination, CursorPagination):
    def get_paginated_response(self, data: PaginatedData) -> Response:
        return Response(self._get_base_paginated_response_data(data))


class HundredPageSizePaginator(PathPrefixedPagePagination):
    page_size = 100


class FiftyPageSizePaginator(PathPrefixedPagePagination):
    page_size = 50


class TwentyFivePageSizePaginator(PathPrefixedPagePagination):
    page_size = 25


class FifteenPageSizePaginator(PathPrefixedPagePagination):
    page_size = 15


class TwentyFiveCursorPaginator(PathPrefixedCursorPagination):
    page_size = 25
    ordering = "-pk"
