from rest_framework.pagination import PageNumberPagination


class HundredPageSizePaginator(PageNumberPagination):
    page_size = 100


class FiftyPageSizePaginator(PageNumberPagination):
    page_size = 50


class TwentyFivePageSizePaginator(PageNumberPagination):
    page_size = 25
