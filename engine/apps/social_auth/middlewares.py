import logging

from django.http import HttpResponse
from django.shortcuts import redirect
from rest_framework import status
from social_core import exceptions
from social_django.middleware import SocialAuthExceptionMiddleware

from apps.grafana_plugin.ui_url_builder import UIURLBuilder
from apps.social_auth.backends import LoginSlackOAuth2V2
from apps.social_auth.exceptions import InstallMultiRegionSlackException
from common.constants.slack_auth import REDIRECT_AFTER_SLACK_INSTALL, SLACK_AUTH_FAILED, SLACK_REGION_ERROR

logger = logging.getLogger(__name__)


class SocialAuthAuthCanceledExceptionMiddleware(SocialAuthExceptionMiddleware):
    def process_exception(self, request, exception):
        backend = getattr(exception, "backend", None)
        url_builder = UIURLBuilder(request.user.organization)
        redirect_to = UIURLBuilder.OnCallPage.CHATOPS

        if backend is not None and isinstance(backend, LoginSlackOAuth2V2):
            redirect_to = UIURLBuilder.OnCallPage.USER_PROFILE

        if exception:
            logger.warning(f"SocialAuthAuthCanceledExceptionMiddleware.process_exception: {exception}")

        if isinstance(exception, exceptions.AuthCanceled):
            # if user canceled authentication, redirect them to the previous page using the same link
            # as we used to redirect after auth/install
            return redirect(url_builder.build_absolute_plugin_ui_url(redirect_to))
        elif isinstance(exception, exceptions.AuthFailed):
            # if authentication was failed, redirect user to the plugin page using the same link
            # as we used to redirect after auth/install with error flag
            return redirect(
                url_builder.build_absolute_plugin_ui_url(redirect_to, path_extra=f"?slack_error={SLACK_AUTH_FAILED}")
            )
        elif isinstance(exception, KeyError) and REDIRECT_AFTER_SLACK_INSTALL in exception.args:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)
        elif isinstance(exception, InstallMultiRegionSlackException):
            return redirect(
                url_builder.build_absolute_plugin_ui_url(
                    redirect_to, path_extra=f"?tab=Slack&slack_error={SLACK_REGION_ERROR}"
                )
            )
