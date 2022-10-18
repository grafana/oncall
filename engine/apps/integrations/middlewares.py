import logging

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework import status

logger = logging.getLogger(__name__)


class IntegrationExceptionMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if request.path.startswith("/integrations/v1") and isinstance(exception, PermissionDenied):
            return HttpResponse(exception, status=status.HTTP_403_FORBIDDEN)
