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
from apps.social_auth.backends import LoginSlackOAuth2V2

logger = logging.getLogger(__name__)


@api_view(["GET"])
@authentication_classes([PluginAuthentication])
@never_cache
@psa("social:complete")
def overridden_login_social_auth(request: Request, backend: str) -> Response:
    # We can't just redirect frontend here because we need to make a API call and pass tokens to this view from JS.
    # So frontend can't follow our redirect.
    # So wrapping and returning URL to redirect as a string.
    if "slack" in backend and settings.SLACK_INTEGRATION_MAINTENANCE_ENABLED:
        return Response(
            "Grafana OnCall is temporary unable to connect your slack account or install OnCall to your slack workspace",
            status=400,
        )

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
