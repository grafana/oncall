import logging
import re

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
            if request.META["QUERY_STRING"]:
                url = f"{url}?{request.META['QUERY_STRING']}"

            regex = re.compile("^HTTP_")
            headers = dict(
                (regex.sub("", header), value) for (header, value) in request.META.items() if header.startswith("HTTP_")
            )
            headers.pop("HOST", None)
            if request.META["CONTENT_TYPE"]:
                headers["CONTENT_TYPE"] = request.META["CONTENT_TYPE"]

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
