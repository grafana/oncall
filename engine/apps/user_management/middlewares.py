import logging
import re

import requests
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR

from apps.user_management.models.region import OrganizationMovedException
from common.api_helpers.utils import create_engine_url

logger = logging.getLogger(__name__)


class OrganizationMovedMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if isinstance(exception, OrganizationMovedException):
            region = exception.organization.migration_destination
            if not region.oncall_backend_url:
                return HttpResponse(
                    "Organization migration destination undefined URL", status=HTTP_500_INTERNAL_SERVER_ERROR
                )

            url = create_engine_url(request.path, override_base=region.oncall_backend_url)
            if request.META["QUERY_STRING"]:
                url = f"{url}?{request.META['QUERY_STRING']}"

            regex = re.compile("^HTTP_")
            headers = dict(
                (regex.sub("", header), value) for (header, value) in request.META.items() if header.startswith("HTTP_")
            )

            if request.method == "GET":
                response = requests.get(url, headers=headers)
            elif request.method == "POST":
                response = requests.post(url, data=request.body, headers=headers)
            elif request.method == "PUT":
                response = requests.put(url, data=request.body, headers=headers)
            elif request.method == "DELETE":
                response = requests.delete(url, headers=headers)
            elif request.method == "OPTIONS":
                response = requests.options(url, headers=headers)

            return HttpResponse(response.content, status=response.status_code)
