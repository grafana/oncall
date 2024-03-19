import logging
import typing

# from django.shortcuts import redirect
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

# def redirect_if_no_refresh_token(backend: typing.Type[BaseAuth], response: Response, *args, **kwargs):
#     """
#     https://python-social-auth.readthedocs.io/en/latest/use_cases.html#re-prompt-google-oauth2-users-to-refresh-the-refresh-token
#     """
#     social = kwargs.get("social")

#     if backend.name == "google-oauth2" and social and response.get("refresh_token") is None and social.extra_data.get("refresh_token") is None:
#         return redirect("/login/google-oauth2?approval_prompt=force")
