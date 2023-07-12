import logging

import requests
from django.http import HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework import status

from common.api_helpers.utils import create_engine_url

from .exceptions import OrganizationDeletedException, OrganizationMovedException

logger = logging.getLogger(__name__)


class OrganizationMovedMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if isinstance(exception, OrganizationMovedException):
            region = exception.organization.migration_destination
            if not region.oncall_backend_url:
                return HttpResponse(
                    "Organization migration destination undefined URL", status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            url = create_engine_url(request.path, override_base=region.oncall_backend_url)
            if (v := request.META.get("QUERY_STRING", None)) is not None:
                url = f"{url}?{v}"

            headers = {}
            if (v := request.META.get("CONTENT_TYPE", None)) is not None:
                headers["Content-type"] = v

            if (v := request.META.get("HTTP_AUTHORIZATION", None)) is not None:
                headers["Authorization"] = v

            response = self.make_request(request.method, url, headers, request.body)
            return HttpResponse(response.content, status=response.status_code)

    def make_request(self, method, url, headers, body):
        if method == "GET":
            return requests.get(url, headers=headers)
        elif method == "POST":
            return requests.post(url, data=body, headers=headers)
        elif method == "PUT":
            return requests.put(url, data=body, headers=headers)
        elif method == "DELETE":
            return requests.delete(url, headers=headers)
        elif method == "OPTIONS":
            return requests.options(url, headers=headers)
        elif method == "PATCH":
            return requests.patch(url, data=body, headers=headers)


class OrganizationDeletedMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if isinstance(exception, OrganizationDeletedException):
            # Return drf-shaped not-found response to keep responses consistent
            return JsonResponse(status=status.HTTP_404_NOT_FOUND, data={"detail": "Not found."})
