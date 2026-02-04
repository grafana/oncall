import datetime
import logging
import typing

import jwt
from django.conf import settings
from django.utils import timezone

from apps.zoom.exceptions import ZoomAPIException

if typing.TYPE_CHECKING:
    from apps.user_management.models import Organization

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ZoomEventTokenInvalid(ZoomAPIException):
    """Exception raised when a Zoom event token is invalid."""

    def __init__(self, msg: str = "Invalid Zoom event token"):
        super().__init__(status=401, msg=msg)


class ZoomEventAuthenticator:
    """Authenticator for Zoom webhook events."""

    @staticmethod
    def create_token(organization: typing.Optional["Organization"]) -> str:
        """Create a JWT token for Zoom event authentication."""
        secret = getattr(settings, 'ZOOM_SIGNING_SECRET', settings.SECRET_KEY)
        expiration = timezone.now() + datetime.timedelta(days=30)
        payload = {
            "organization_id": organization.public_primary_key,
            "exp": expiration,
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        return token

    @staticmethod
    def verify(token: str) -> dict:
        """Verify a JWT token from Zoom events."""
        secret = getattr(settings, 'ZOOM_SIGNING_SECRET', settings.SECRET_KEY)
        try:
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            return payload
        except jwt.InvalidTokenError as e:
            logger.error(f"Error while verifying Zoom token: {e}")
            raise ZoomEventTokenInvalid(msg="Invalid token from Zoom server")
