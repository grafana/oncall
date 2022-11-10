import logging

import requests
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework import status

from apps.user_management.models.region import OrganizationMovedException
from common.api_helpers.utils import create_engine_url

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
            if request.META.get("QUERY_STRING", None):
                url = f"{url}?{request.META['QUERY_STRING']}"

            headers = {}
            if request.META.get("CONTENT_TYPE", None):
                headers["Content-type"] = request.META["CONTENT_TYPE"]

            if request.META.get("HTTP_AUTHORIZATION", None):
                headers["Authorization"] = request.META["HTTP_AUTHORIZATION"]

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
