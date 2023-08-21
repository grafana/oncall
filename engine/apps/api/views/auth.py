import logging
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response
from social_core.actions import do_auth, do_complete
from social_django.utils import psa
from social_django.views import _do_login

from apps.auth_token.auth import PluginAuthentication, SlackTokenAuthentication
from apps.social_auth.backends import LoginSlackOAuth2V2

logger = logging.getLogger(__name__)


@api_view(["GET"])
@authentication_classes([PluginAuthentication])
@never_cache
@psa("social:complete")
def overridden_login_slack_auth(request, backend):
    # We can't just redirect frontend here because we need to make a API call and pass tokens to this view from JS.
    # So frontend can't follow our redirect.
    # So wrapping and returning URL to redirect as a string.
    if settings.SLACK_INTEGRATION_MAINTENANCE_ENABLED:
        return Response(
            "Grafana OnCall is temporary unable to connect your slack account or install OnCall to your slack workspace",
            status=400,
        )
    url_to_redirect_to = do_auth(request.backend, redirect_name=REDIRECT_FIELD_NAME).url

    return Response(url_to_redirect_to, 200)


@api_view(["GET"])
@authentication_classes([SlackTokenAuthentication])
@never_cache
@csrf_exempt
@psa("social:complete")
def overridden_complete_slack_auth(request, backend, *args, **kwargs):
    """Authentication complete view"""
    # InstallSlackOAuth2V2 backend
    redirect_to = "/a/grafana-oncall-app/chat-ops"
    if isinstance(request.backend, LoginSlackOAuth2V2):
        # if this was a user login/linking account, redirect to profile
        redirect_to = "/a/grafana-oncall-app/users/me"

    result = do_complete(
        request.backend,
        _do_login,
        user=request.user,
        redirect_name=REDIRECT_FIELD_NAME,
        request=request,
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
