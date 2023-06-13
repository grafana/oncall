import json
import logging

from django.views import View
from rest_framework import permissions
from rest_framework.authentication import get_authorization_header
from rest_framework.request import Request

from apps.auth_token.exceptions import InvalidToken
from apps.grafana_plugin.helpers.gcom import check_token

logger = logging.getLogger(__name__)


class PluginTokenVerified(permissions.BasePermission):
    # The grafana plugin can either use a token from gcom or one generated internally by oncall
    # Tokens from gcom will be prefixed with gcom: otherwise they will be treated as local
    def has_permission(self, request: Request, view: View) -> bool:
        token_string = get_authorization_header(request).decode()
        context = json.loads(request.headers.get("X-Instance-Context"))
        try:
            auth_token = check_token(token_string, context)
            if auth_token:
                return True
        except InvalidToken:
            logger.warning(f"Invalid token used: {context}")

        return False
