from rest_framework.pagination import CursorPagination, PageNumberPagination
from rest_framework.response import Response
from rest_framework.utils.urls import remove_query_param, replace_query_param

from common.api_helpers.utils import create_engine_url


class PathPrefixedPagination(PageNumberPagination):
    def get_next_link(self):
        if not self.page.has_next():
            return None
        url = create_engine_url(self.request.get_full_path())
        page_number = self.page.next_page_number()
        return replace_query_param(url, self.page_query_param, page_number)

    def get_previous_link(self):
        if not self.page.has_previous():
            return None
        url = create_engine_url(self.request.get_full_path())
        page_number = self.page.previous_page_number()
        if page_number == 1:
            return remove_query_param(url, self.page_query_param)
        return replace_query_param(url, self.page_query_param, page_number)

    def get_paginated_response(self, data):
        return Response(
            {
                "links": {"next": self.get_next_link(), "previous": self.get_previous_link()},
                "count": self.page.paginator.count,
                "results": data,
            }
        )


class HundredPageSizePaginator(PathPrefixedPagination):
    page_size = 100


class FiftyPageSizePaginator(PathPrefixedPagination):
    page_size = 50


class TwentyFivePageSizePaginator(PathPrefixedPagination):
    page_size = 25


class TwentyFiveCursorPaginator(CursorPagination):
    page_size = 25
    max_page_size = 100
    page_size_query_param = "perpage"
    ordering = "-pk"
