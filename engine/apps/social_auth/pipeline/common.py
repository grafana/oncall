import typing

from django.http import HttpResponse
from rest_framework import status
from social_core.backends.base import BaseAuth
from social_core.exceptions import AuthForbidden
from social_core.strategy import BaseStrategy

from apps.user_management.models import Organization, User


class UserOrganizationKwargsResponse(typing.TypedDict):
    user: User
    organization: Organization


def set_user_and_organization_from_request(
    backend: typing.Type[BaseAuth], strategy: typing.Type[BaseStrategy], *args, **kwargs
) -> UserOrganizationKwargsResponse:
    user = strategy.request.user
    organization = strategy.request.auth.organization
    if user is None or organization is None:
        return HttpResponse(str(AuthForbidden(backend)), status=status.HTTP_401_UNAUTHORIZED)
    return {
        "user": user,
        "organization": organization,
    }


def delete_auth_token(strategy, *args, **kwargs):
    strategy.request.auth.delete()
