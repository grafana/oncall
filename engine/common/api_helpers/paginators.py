from rest_framework.pagination import CursorPagination, PageNumberPagination

from common.api_helpers.utils import create_engine_url


class PathPrefixedPagination(PageNumberPagination):
    def paginate_queryset(self, queryset, request, view=None):
        request.build_absolute_uri = lambda: create_engine_url(request.get_full_path())
        return super().paginate_queryset(queryset, request, view)


class PathPrefixedCursorPagination(CursorPagination):
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
    max_page_size = 100
    page_size_query_param = "perpage"
    ordering = "-pk"
