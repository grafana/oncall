import logging
import typing

from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication

from apps.mattermost.models import MattermostUser
from apps.mattermost.utils import MattermostEventAuthenticator, MattermostEventTokenInvalid
from apps.user_management.models import User

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class MattermostEventAuthentication(BaseAuthentication):
    def authenticate(self, request) -> typing.Tuple[User, None]:
        if "context" not in request.data or "token" not in request.data["context"]:
            raise exceptions.AuthenticationFailed("Auth token is missing")

        auth = request.data["context"]["token"]
        try:
            MattermostEventAuthenticator.verify(auth)
            mattermost_user = MattermostUser.objects.get(mattermost_user_id=request.data["user_id"])
        except MattermostEventTokenInvalid:
            raise exceptions.AuthenticationFailed("Invalid auth token")
        except MattermostUser.DoesNotExist:
            raise exceptions.AuthenticationFailed("Mattermost user not integrated")

        return mattermost_user.user, None
