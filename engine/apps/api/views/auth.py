import logging
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.request import Request
from rest_framework.response import Response
from social_core.actions import do_auth, do_complete, do_disconnect
from social_core.backends.google import GoogleOAuth2
from social_django.utils import psa
from social_django.views import _do_login

from apps.auth_token.auth import GoogleTokenAuthentication, PluginAuthentication, SlackTokenAuthentication
from apps.chatops_proxy.utils import (
    get_installation_link_from_chatops_proxy,
    get_slack_oauth_response_from_chatops_proxy,
)
from apps.slack.installation import install_slack_integration
from apps.social_auth.backends import SLACK_INSTALLATION_BACKEND, LoginSlackOAuth2V2

logger = logging.getLogger(__name__)


@api_view(["GET"])
@authentication_classes([PluginAuthentication])
@never_cache
@psa("social:complete")
def overridden_login_social_auth(request: Request, backend: str) -> Response:
    """
    overridden_login_social_auth starts the installation of integration which uses OAuth flow.
    """

    # We can't just redirect frontend here because we need to make a API call and pass tokens to this view from JS.
    # So frontend can't follow our redirect.
    # So wrapping and returning URL to redirect as a string.
    if "slack" in backend and settings.SLACK_INTEGRATION_MAINTENANCE_ENABLED:
        return Response(
            "Grafana OnCall is temporary unable to connect your slack account or install OnCall to your slack workspace",
            status=400,
        )

    if backend == SLACK_INSTALLATION_BACKEND and settings.UNIFIED_SLACK_APP_ENABLED:
        """
        Install unified slack integration via chatops-proxy.
        1. Get installation link from chatops-proxy
        2. If link is not None – slack installation already exists on Chatops-Proxy - install using it's oauth response.
        """
        try:
            link = get_installation_link_from_chatops_proxy(request.user)
            if link is not None:
                return Response(link, 200)
            else:
                slack_oauth_response = get_slack_oauth_response_from_chatops_proxy(request.user.organization.stack_id)
                install_slack_integration(request.user.organization, request.user, slack_oauth_response)
                return Response("slack integration installed", 201)
        except Exception as e:
            logger.exception("overridden_login_social_auth: Failed to install slack via chatops-proxy: %s", e)
            return Response({"error": "something went wrong, try again later"}, 500)
    else:
        # Otherwise use social-auth.
        url_to_redirect_to = do_auth(request.backend, redirect_name=REDIRECT_FIELD_NAME).url
    return Response(url_to_redirect_to, 200)


@api_view(["GET"])
@authentication_classes([GoogleTokenAuthentication, SlackTokenAuthentication])
@never_cache
@csrf_exempt
@psa("social:complete")
def overridden_complete_social_auth(request: Request, backend: str, *args, **kwargs) -> Response:
    """Authentication complete view"""
    if isinstance(request.backend, (LoginSlackOAuth2V2, GoogleOAuth2)):
        # if this was a user login/linking account, redirect to profile
        redirect_to = "/a/grafana-oncall-app/users/me"
    else:
        # InstallSlackOAuth2V2 backend
        redirect_to = "/a/grafana-oncall-app/chat-ops"

    kwargs.update(
        user=request.user,
        redirect_name=REDIRECT_FIELD_NAME,
        request=request,
    )
    result = do_complete(
        request.backend,
        _do_login,
        *args,
        **kwargs,
    )

    # handle potential errors in the strategy pipeline
    return_to = None
    if isinstance(result, HttpResponse):
        # check if there was a redirect set in the session
        return_to = request.backend.strategy.session.get(REDIRECT_FIELD_NAME)

    if return_to is None:
        # We build the frontend url using org url since multiple stacks could be connected to one backend.
        return_to = urljoin(request.user.organization.grafana_url, redirect_to)
    return HttpResponseRedirect(return_to)


@api_view(["GET"])
@authentication_classes([PluginAuthentication])
@never_cache
@psa("social:disconnect")
def overridden_disconnect_social_auth(request: Request, backend: str) -> Response:
    if backend == "google-oauth2":
        do_disconnect(request.backend, request.user)
    return Response("ok", 200)
