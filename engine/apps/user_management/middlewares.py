import logging
import re

import requests
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

from apps.user_management.models.region import OrganizationMovedException
from common.api_helpers.utils import create_engine_url

logger = logging.getLogger(__name__)


class OrganizationMovedMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if isinstance(exception, OrganizationMovedException):
            region = exception.organization.migration_destination
            url = create_engine_url(request.path, override_base=region.oncall_backend_url)
            if request.META['QUERY_STRING']:
                url = f"{url}?{request.META['QUERY_STRING']}"

            regex = re.compile('^HTTP_')
            headers = dict(
                (regex.sub('', header), value) for (header, value) in request.META.items() if header.startswith('HTTP_')
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

            response.raise_for_status()

            return HttpResponse(response.content, status=response.status_code)

