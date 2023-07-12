from rest_framework.pagination import CursorPagination, PageNumberPagination

from common.api_helpers.utils import create_engine_url

MAX_PAGE_SIZE = 100
PAGE_QUERY_PARAM = "page"
PAGE_SIZE_QUERY_PARAM = "perpage"


class PathPrefixedPagination(PageNumberPagination):
    max_page_size = MAX_PAGE_SIZE
    page_query_param = PAGE_QUERY_PARAM
    page_size_query_param = PAGE_SIZE_QUERY_PARAM

    def paginate_queryset(self, queryset, request, view=None):
        request.build_absolute_uri = lambda: create_engine_url(request.get_full_path())
        return super().paginate_queryset(queryset, request, view)


class PathPrefixedCursorPagination(CursorPagination):
    max_page_size = MAX_PAGE_SIZE
    page_query_param = PAGE_QUERY_PARAM
    page_size_query_param = PAGE_SIZE_QUERY_PARAM

    def paginate_queryset(self, queryset, request, view=None):
        request.build_absolute_uri = lambda: create_engine_url(request.get_full_path())
        return super().paginate_queryset(queryset, request, view)


class HundredPageSizePaginator(PathPrefixedPagination):
    page_size = 100


class FiftyPageSizePaginator(PathPrefixedPagination):
    page_size = 50


class TwentyFivePageSizePaginator(PathPrefixedPagination):
    page_size = 25


class FifteenPageSizePaginator(PathPrefixedPagination):
    page_size = 15


class TwentyFiveCursorPaginator(PathPrefixedCursorPagination):
    page_size = 25
    ordering = "-pk"
