from typing import Tuple

from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication

from apps.auth_token.exceptions import InvalidToken
from apps.user_management.models import Organization

from .models import MattermostAuthToken


class MattermostAuthTokenAuthentication(BaseAuthentication):
    model = MattermostAuthToken

    def extract_auth_token(self, request) -> str:
        return request.query_params.get("auth_token")

    def authenticate(self, request) -> Tuple[Organization, MattermostAuthToken]:
        auth = self.extract_auth_token(request=request)
        organization, auth_token = self.authenticate_credentials(auth)
        return organization, auth_token

    def authenticate_credentials(self, token_string: str) -> Tuple[Organization, MattermostAuthToken]:
        try:
            auth_token = self.model.validate_token_string(token_string)
        except InvalidToken:
            raise exceptions.AuthenticationFailed("Invalid auth token")

        return auth_token.organization, auth_token


class MattermostWebhookAuthTokenAuthentication(MattermostAuthTokenAuthentication):
    def extract_auth_token(self, request) -> str:
        return request.data.get("state", {}).get("auth_token", "")
