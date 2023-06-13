from typing import Optional, Tuple

from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, get_authorization_header

from apps.auth_token.exceptions import InvalidToken
from apps.user_management.models import User

from .models import MobileAppAuthToken, MobileAppVerificationToken


class MobileAppVerificationTokenAuthentication(BaseAuthentication):
    model = MobileAppVerificationToken

    def authenticate(self, request) -> Tuple[User, MobileAppVerificationToken]:
        auth = get_authorization_header(request).decode("utf-8")
        user, auth_token = self.authenticate_credentials(auth)
        return user, auth_token

    def authenticate_credentials(self, token_string: str) -> Tuple[User, MobileAppVerificationToken]:
        try:
            auth_token = self.model.validate_token_string(token_string)
        except InvalidToken:
            raise exceptions.AuthenticationFailed("Invalid token")

        return auth_token.user, auth_token


class MobileAppAuthTokenAuthentication(BaseAuthentication):
    model = MobileAppAuthToken

    def authenticate(self, request) -> Optional[Tuple[User, MobileAppAuthToken]]:
        auth = get_authorization_header(request).decode("utf-8")
        user, auth_token = self.authenticate_credentials(auth)
        if user is None:
            return None
        return user, auth_token

    def authenticate_credentials(self, token_string: str) -> Tuple[Optional[User], Optional[MobileAppAuthToken]]:
        try:
            auth_token = self.model.validate_token_string(token_string)
        except InvalidToken:
            return None, None

        return auth_token.user, auth_token
