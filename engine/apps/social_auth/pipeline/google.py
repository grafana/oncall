import logging
import typing

import requests
from rest_framework.response import Response
from social_core.backends.base import BaseAuth

from apps.user_management.models import User

logger = logging.getLogger(__name__)


def persist_access_and_refresh_tokens(backend: typing.Type[BaseAuth], response: Response, user: User, *args, **kwargs):
    """
    TODO: what happens if `refresh_token` is not present? what are the scenarios that lead to this?

    NOTE: I think it's only included when the user initially grants access to our Google OAuth2 app
    on subsequent logins, the refresh_token is not included in the response, only access_token.. what to do here?

    https://medium.com/starthinker/google-oauth-2-0-access-token-and-refresh-token-explained-cccf2fc0a6d9
    """
    user.finish_google_oauth2_connection_flow(response)


def disconnect_user_google_oauth2_settings(backend: typing.Type[BaseAuth], user: User, *args, **kwargs):
    """
    Don't use `google_oauth2_user.access_token` when revoking token, use `refresh_token` instead. If we use
    the access token, we may get an HTTP 400 from Google because the token may be invalid or revoked.

    https://stackoverflow.com/a/18578660/3902555
    """
    user_pk = user.pk
    google_oauth2_user = user.google_oauth2_user

    logger.info(f"Disconnecting user {user_pk} from Google OAuth2")

    try:
        backend.revoke_token(google_oauth2_user.refresh_token, google_oauth2_user.google_user_id)
    except requests.exceptions.HTTPError as e:
        response = e.response

        logger.error(f"There was an HTTP error when trying to revoke Google OAuth2 token for user={user_pk}")

        if response.status_code == 400:
            error_details = response.json()
            error_code = error_details["error"]
            error_description = error_details["error_description"]

            logger.error(
                f"There was an HTTP 400 error when trying to revoke Google OAuth2 token for user={user_pk} "
                f"error_code={error_code} error_description={error_description}"
            )

            error_codes_to_ignore = ["invalid_token"]

            if error_code not in error_codes_to_ignore:
                raise e
            else:
                logger.info(f"Google OAuth2 token for user {user_pk} is already invalid or revoked, ignoring error")

    user.finish_google_oauth2_disconnection_flow()

    logger.info(f"Successfully disconnected user {user.pk} from Google OAuth2")
