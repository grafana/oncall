import logging

from django.shortcuts import redirect
logger = logging.getLogger(__name__)

def google_oauth_testing(*args, **kwargs):
    # TODO: persist auth_token and refresh_token here
    print("google_oauth_testing", args, kwargs)


def redirect_if_no_refresh_token(backend, response, *args, **kwargs):
    """
    https://python-social-auth.readthedocs.io/en/latest/use_cases.html#re-prompt-google-oauth2-users-to-refresh-the-refresh-token
    """
    social = kwargs.get("social")
    print("redirect_if_no_refresh_token", backend, response, social, args, kwargs)

    if backend.name == "google-oauth2" and social and response.get("refresh_token") is None and social.extra_data.get("refresh_token") is None:
        return redirect("/login/google-oauth2?approval_prompt=force")
