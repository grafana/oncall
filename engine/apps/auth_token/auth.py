import json
import logging
from typing import Tuple

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.request import Request

from apps.api.permissions import GrafanaAPIPermission, LegacyAccessControlRole, RBACPermission, user_is_authorized
from apps.grafana_plugin.helpers.gcom import check_token
from apps.user_management.exceptions import OrganizationDeletedException, OrganizationMovedException
from apps.user_management.models import User
from apps.user_management.models.organization import Organization
from settings.base import SELF_HOSTED_SETTINGS

from .constants import SCHEDULE_EXPORT_TOKEN_NAME, SLACK_AUTH_TOKEN_NAME
from .exceptions import InvalidToken
from .grafana.grafana_auth_token import get_service_account_token_permissions
from .models import ApiAuthToken, PluginAuthToken, ScheduleExportAuthToken, SlackAuthToken, UserScheduleExportAuthToken

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ApiTokenAuthentication(BaseAuthentication):
    model = ApiAuthToken

    def authenticate(self, request):
        auth = get_authorization_header(request).decode("utf-8")
        user, auth_token = self.authenticate_credentials(auth)

        if not user_is_authorized(user, [RBACPermission.Permissions.API_KEYS_WRITE]):
            raise exceptions.AuthenticationFailed(
                "Only users with Admin permissions are allowed to perform this action."
            )

        return user, auth_token

    def authenticate_credentials(self, token):
        """
        Due to the random nature of hashing a  value, this must inspect
        each auth_token individually to find the correct one.
        """
        try:
            auth_token = self.model.validate_token_string(token)
        except InvalidToken:
            raise exceptions.AuthenticationFailed("Invalid token.")

        if auth_token.organization.is_moved:
            raise OrganizationMovedException(auth_token.organization)
        if auth_token.organization.deleted_at:
            raise OrganizationDeletedException(auth_token.organization)

        return auth_token.user, auth_token


class BasePluginAuthentication(BaseAuthentication):
    """
    Authentication used by grafana-plugin app where we tolerate user not being set yet due to being in
    a state of initialization, Only validates that the plugin should be talking to the backend. Outside of
    this app PluginAuthentication should be used since it also checks the user.
    """

    def authenticate_header(self, request):
        # Check parent's method comments
        return "Bearer"

    def authenticate(self, request: Request) -> Tuple[User, PluginAuthToken]:
        token_string = get_authorization_header(request).decode()

        if not token_string:
            raise exceptions.AuthenticationFailed("No token provided")

        return self.authenticate_credentials(token_string, request)

    def authenticate_credentials(self, token_string: str, request: Request) -> Tuple[User, PluginAuthToken]:
        context_string = request.headers.get("X-Instance-Context")
        if not context_string:
            raise exceptions.AuthenticationFailed("No instance context provided.")

        try:
            context = dict(json.loads(context_string))
        except (ValueError, TypeError):
            raise exceptions.AuthenticationFailed("Instance context must be JSON dict.")

        if "stack_id" not in context or "org_id" not in context:
            raise exceptions.AuthenticationFailed("Invalid instance context.")

        try:
            auth_token = check_token(token_string, context=context)
            if not auth_token.organization:
                raise exceptions.AuthenticationFailed("No organization associated with token.")
        except InvalidToken:
            raise exceptions.AuthenticationFailed("Invalid token.")

        user = self._get_user(request, auth_token.organization)
        return user, auth_token

    @staticmethod
    def _get_user(request: Request, organization: Organization) -> User:
        try:
            context = dict(json.loads(request.headers.get("X-Grafana-Context")))
        except (ValueError, TypeError):
            logger.info("auth request user not found - missing valid X-Grafana-Context")
            return None

        if "UserId" not in context and "UserID" not in context:
            logger.info("auth request user not found - X-Grafana-Context missing UserID")
            return None

        try:
            user_id = context["UserId"]
        except KeyError:
            user_id = context["UserID"]

        try:
            return organization.users.get(user_id=user_id)
        except User.DoesNotExist:
            logger.info(f"auth request user not found - user_id={user_id}")
            return None


class PluginAuthentication(BasePluginAuthentication):
    @staticmethod
    def _get_user(request: Request, organization: Organization) -> User:
        try:
            context = dict(json.loads(request.headers.get("X-Grafana-Context")))
        except (ValueError, TypeError):
            raise exceptions.AuthenticationFailed("Grafana context must be JSON dict.")

        if "UserId" not in context and "UserID" not in context:
            raise exceptions.AuthenticationFailed("Invalid Grafana context.")

        try:
            user_id = context["UserId"]
        except KeyError:
            user_id = context["UserID"]

        try:
            return organization.users.get(user_id=user_id)
        except User.DoesNotExist:
            logger.debug(f"Could not get user from grafana request. Context {context}")
            raise exceptions.AuthenticationFailed("Non-existent or anonymous user.")


class PluginAuthenticationSchema(OpenApiAuthenticationExtension):
    target_class = PluginAuthentication
    name = "PluginAuthentication"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": (
                "Additional X-Instance-Context and X-Grafana-Context headers must be set. "
                "THIS WILL NOT WORK IN SWAGGER UI."
            ),
        }


class GrafanaIncidentUser(AnonymousUser):
    @property
    def is_authenticated(self):
        # Always return True. This is a way to tell if
        # the user has been authenticated in permissions
        return True


class GrafanaIncidentStaticKeyAuth(BaseAuthentication):
    def authenticate_header(self, request):  # noqa
        # Check parent's method comments
        return "Bearer"

    def authenticate(self, request: Request) -> Tuple[GrafanaIncidentUser, None]:
        token_string = get_authorization_header(request).decode()

        if (
            not token_string == settings.GRAFANA_INCIDENT_STATIC_API_KEY
            or settings.GRAFANA_INCIDENT_STATIC_API_KEY is None
        ):
            raise exceptions.AuthenticationFailed("Wrong token")

        if not token_string:
            raise exceptions.AuthenticationFailed("No token provided")

        return self.authenticate_credentials(token_string, request)

    def authenticate_credentials(self, token_string: str, request: Request) -> Tuple[GrafanaIncidentUser, None]:
        try:
            user = GrafanaIncidentUser()
        except InvalidToken:
            raise exceptions.AuthenticationFailed("Invalid token.")

        return user, None


class SlackTokenAuthentication(BaseAuthentication):
    model = SlackAuthToken

    def authenticate(self, request) -> Tuple[User, SlackAuthToken]:
        auth = request.query_params.get(SLACK_AUTH_TOKEN_NAME)
        if not auth:
            raise exceptions.AuthenticationFailed("Invalid token.")
        user, auth_token = self.authenticate_credentials(auth)
        return user, auth_token

    def authenticate_credentials(self, token_string: str) -> Tuple[User, SlackAuthToken]:
        try:
            auth_token = self.model.validate_token_string(token_string)
        except InvalidToken:
            raise exceptions.AuthenticationFailed("Invalid token.")

        return auth_token.user, auth_token


class ScheduleExportAuthentication(BaseAuthentication):
    model = ScheduleExportAuthToken

    def authenticate(self, request) -> Tuple[User, ScheduleExportAuthToken]:
        auth = request.query_params.get(SCHEDULE_EXPORT_TOKEN_NAME)
        public_primary_key = request.parser_context.get("kwargs", {}).get("pk")
        if not auth:
            raise exceptions.AuthenticationFailed("Invalid token.")

        auth_token = self.authenticate_credentials(auth, public_primary_key)
        return auth_token

    def authenticate_credentials(
        self, token_string: str, public_primary_key: str
    ) -> Tuple[User, ScheduleExportAuthToken]:
        try:
            auth_token = self.model.validate_token_string(token_string)
        except InvalidToken:
            raise exceptions.AuthenticationFailed("Invalid token.")

        if auth_token.organization.is_moved:
            raise OrganizationMovedException(auth_token.organization)
        if auth_token.organization.deleted_at:
            raise OrganizationDeletedException(auth_token.organization)

        if auth_token.schedule.public_primary_key != public_primary_key:
            raise exceptions.AuthenticationFailed("Invalid schedule export token for schedule")

        if not auth_token.active:
            raise exceptions.AuthenticationFailed("Export token is deactivated")

        return auth_token.user, auth_token


class UserScheduleExportAuthentication(BaseAuthentication):
    model = UserScheduleExportAuthToken

    def authenticate(self, request) -> Tuple[User, UserScheduleExportAuthToken]:
        auth = request.query_params.get(SCHEDULE_EXPORT_TOKEN_NAME)
        public_primary_key = request.parser_context.get("kwargs", {}).get("pk")

        if not auth:
            raise exceptions.AuthenticationFailed("Invalid token.")

        auth_token = self.authenticate_credentials(auth, public_primary_key)
        return auth_token

    def authenticate_credentials(
        self, token_string: str, public_primary_key: str
    ) -> Tuple[User, UserScheduleExportAuthToken]:
        try:
            auth_token = self.model.validate_token_string(token_string)
        except InvalidToken:
            raise exceptions.AuthenticationFailed("Invalid token")

        if auth_token.organization.is_moved:
            raise OrganizationMovedException(auth_token.organization)
        if auth_token.organization.deleted_at:
            raise OrganizationDeletedException(auth_token.organization)

        if auth_token.user.public_primary_key != public_primary_key:
            raise exceptions.AuthenticationFailed("Invalid schedule export token for user")

        if not auth_token.active:
            raise exceptions.AuthenticationFailed("Export token is deactivated")

        return auth_token.user, auth_token


X_GRAFANA_INSTANCE_ID = "X-Grafana-Instance-ID"
GRAFANA_SA_PREFIX = "glsa_"


class GrafanaServiceAccountAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth = get_authorization_header(request).decode("utf-8")
        if not auth:
            raise exceptions.AuthenticationFailed("Invalid token.")
        if not auth.startswith(GRAFANA_SA_PREFIX):
            return None

        organization = self.get_organization(request)
        if not organization:
            raise exceptions.AuthenticationFailed("Invalid organization.")
        if organization.is_moved:
            raise OrganizationMovedException(organization)
        if organization.deleted_at:
            raise OrganizationDeletedException(organization)

        return self.authenticate_credentials(organization, auth)

    def get_organization(self, request):
        if settings.LICENSE == settings.CLOUD_LICENSE_NAME:
            instance_id = request.headers.get(X_GRAFANA_INSTANCE_ID)
            if not instance_id:
                raise exceptions.AuthenticationFailed(f"Missing {X_GRAFANA_INSTANCE_ID}")
            return Organization.objects.filter(stack_id=instance_id).first()
        else:
            org_slug = SELF_HOSTED_SETTINGS["ORG_SLUG"]
            instance_slug = SELF_HOSTED_SETTINGS["STACK_SLUG"]
            return Organization.objects.filter(org_slug=org_slug, stack_slug=instance_slug).first()

    def authenticate_credentials(self, organization, token):
        permissions = get_service_account_token_permissions(organization, token)
        if not permissions:
            raise exceptions.AuthenticationFailed("Invalid token.")

        role = LegacyAccessControlRole.NONE
        if not organization.is_rbac_permissions_enabled:
            role = self.determine_role_from_permissions(permissions)

        user = User(
            organization_id=organization.pk,
            name="Grafana Service Account",
            username="grafana_service_account",
            role=role,
            permissions=[GrafanaAPIPermission(action=key) for key, _ in permissions.items()],
        )

        auth_token = ApiAuthToken(organization=organization, user=user, name="Grafana Service Account")

        return user, auth_token

    # Using default permissions as proxies for roles since we cannot explicitly get role from the service account token
    def determine_role_from_permissions(self, permissions):
        if "plugins:write" in permissions:
            return LegacyAccessControlRole.ADMIN
        if "dashboards:write" in permissions:
            return LegacyAccessControlRole.EDITOR
        if "dashboards:read" in permissions:
            return LegacyAccessControlRole.VIEWER
        return LegacyAccessControlRole.NONE
