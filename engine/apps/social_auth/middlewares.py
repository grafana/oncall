import logging
from urllib.parse import urljoin

from django.http import HttpResponse
from django.shortcuts import redirect
from rest_framework import status
from social_core import exceptions
from social_django.middleware import SocialAuthExceptionMiddleware

from apps.social_auth.backends import LoginSlackOAuth2V2
from apps.social_auth.exceptions import InstallMultiRegionSlackException
from common.constants.slack_auth import REDIRECT_AFTER_SLACK_INSTALL, SLACK_AUTH_FAILED

logger = logging.getLogger(__name__)


class SocialAuthAuthCanceledExceptionMiddleware(SocialAuthExceptionMiddleware):
    def process_exception(self, request, exception):
        backend = getattr(exception, "backend", None)
        redirect_to = "/a/grafana-oncall-app/chat-ops"
        if backend is not None and isinstance(backend, LoginSlackOAuth2V2):
            redirect_to = "/a/grafana-oncall-app/users/me"
        if exception:
            logger.warning(f"SocialAuthAuthCanceledExceptionMiddleware.process_exception: {exception}")
        if isinstance(exception, exceptions.AuthCanceled):
            # if user canceled authentication, redirect them to the previous page using the same link
            # as we used to redirect after auth/install
            url_to_redirect = urljoin(request.user.organization.grafana_url, redirect_to)
            return redirect(url_to_redirect)
        elif isinstance(exception, exceptions.AuthFailed):
            # if authentication was failed, redirect user to the plugin page using the same link
            # as we used to redirect after auth/install with error flag
            url_to_redirect = urljoin(
                request.user.organization.grafana_url, f"{redirect_to}&slack_error={SLACK_AUTH_FAILED}"
            )
            return redirect(url_to_redirect)
        elif isinstance(exception, KeyError) and REDIRECT_AFTER_SLACK_INSTALL in exception.args:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)
        elif isinstance(exception, InstallMultiRegionSlackException):
            REGION_ERROR = "region_error"
            url_to_redirect = urljoin(
                request.user.organization.grafana_url, f"{redirect_to}?tab=Slack&slack_error={REGION_ERROR}"
            )
            return redirect(url_to_redirect)
