from urllib.parse import urljoin

from django.http import HttpResponse
from django.shortcuts import redirect
from rest_framework import status
from social_core import exceptions
from social_django.middleware import SocialAuthExceptionMiddleware

from common.constants.slack_auth import REDIRECT_AFTER_SLACK_INSTALL, SLACK_AUTH_FAILED


class SocialAuthAuthCanceledExceptionMiddleware(SocialAuthExceptionMiddleware):
    def process_exception(self, request, exception):
        if isinstance(exception, exceptions.AuthCanceled):
            # if user canceled authentication, redirect them to the previous page using the same link
            # as we used to redirect after auth/install
            return redirect(request.session[REDIRECT_AFTER_SLACK_INSTALL])
        elif isinstance(exception, exceptions.AuthFailed):
            # if authentication was failed, redirect user to the plugin page using the same link
            # as we used to redirect after auth/install with error flag
            url_to_redirect = urljoin(
                request.session[REDIRECT_AFTER_SLACK_INSTALL], f"?page=chat-ops&slack_error={SLACK_AUTH_FAILED}"
            )
            return redirect(url_to_redirect)
        elif isinstance(exception, KeyError) and REDIRECT_AFTER_SLACK_INSTALL in exception.args:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)
