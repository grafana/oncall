import datetime
import logging
import typing

import jwt
from django.conf import settings
from django.utils import timezone

from apps.mattermost.exceptions import MattermostEventTokenInvalid

if typing.TYPE_CHECKING:
    from apps.user_management.models import Organization

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class MattermostEventAuthenticator:
    @staticmethod
    def create_token(organization: typing.Optional["Organization"]):
        secret = settings.MATTERMOST_SIGNING_SECRET
        expiration = timezone.now() + datetime.timedelta(days=30)
        payload = {
            "organization_id": organization.public_primary_key,
            "exp": expiration,
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        return token

    @staticmethod
    def verify(token: str):
        secret = settings.MATTERMOST_SIGNING_SECRET
        try:
            payload = jwt.decode(token, secret, algorithms="HS256")
            return payload
        except jwt.InvalidTokenError as e:
            logger.error(f"Error while verifying mattermost token {e}")
            raise MattermostEventTokenInvalid(msg="Invalid token from mattermost server")
