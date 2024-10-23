import binascii
from hmac import compare_digest

from django.db import models

from apps.api.permissions import GrafanaAPIPermissions, LegacyAccessControlRole
from apps.auth_token import constants
from apps.auth_token.crypto import hash_token_string
from apps.auth_token.exceptions import InvalidToken
from apps.auth_token.grafana.grafana_auth_token import (
    get_service_account_details,
    get_service_account_token_permissions,
)
from apps.auth_token.models import BaseAuthToken
from apps.user_management.models import ServiceAccount, ServiceAccountUser


class ServiceAccountToken(BaseAuthToken):
    GRAFANA_SA_PREFIX = "glsa_"

    service_account: "ServiceAccount"
    service_account = models.ForeignKey(ServiceAccount, on_delete=models.CASCADE, related_name="tokens")

    class Meta:
        unique_together = ("token_key", "service_account", "digest")

    @property
    def organization(self):
        return self.service_account.organization

    @classmethod
    def validate_token(cls, organization, token):
        # get permissions and confirm token is valid
        permissions = get_service_account_token_permissions(organization, token)
        if not permissions:
            # TODO: if token in DB, mark as revoked? (NOTE: a token can be disabled/re-enabled)
            #       consider revoking at the oncall side too?
            raise InvalidToken

        # check if we have already seen this token
        validated_token = None
        service_account = None
        prefix_length = len(cls.GRAFANA_SA_PREFIX)
        token_key = token[prefix_length : prefix_length + constants.TOKEN_KEY_LENGTH]
        try:
            hashable_token = binascii.hexlify(token.encode()).decode()
            digest = hash_token_string(hashable_token)
        except (TypeError, binascii.Error):
            raise InvalidToken
        for existing_token in cls.objects.filter(service_account__organization=organization, token_key=token_key):
            if compare_digest(digest, existing_token.digest):
                validated_token = existing_token
                service_account = existing_token.service_account
                break

        if not validated_token:
            # create a token
            # make request to api/user using token
            service_account_data = get_service_account_details(organization, token)
            if not service_account_data:
                # older grafana versions return 403 trying to get user details with service account token
                # use some default values
                service_account_data = {
                    "login": "grafana_service_account",
                    "uid": None,  # "service-account:7"
                }

            grafana_id = None
            if service_account_data["uid"] is not None:
                try:
                    grafana_id = int(service_account_data["uid"].split(":")[-1])
                except ValueError:
                    pass

            # get or create service account
            service_account, _ = ServiceAccount.objects.get_or_create(
                organization=organization,
                grafana_id=grafana_id,
                defaults={
                    "login": service_account_data["login"],
                },
            )
            # create token
            validated_token = cls.objects.get_or_create(
                service_account=service_account,
                token_key=token_key,
                digest=digest,
            )

        def _determine_role_from_permissions(permissions):
            # Using default permissions as proxies for roles since
            # we cannot explicitly get role from the service account token
            if "plugins:write" in permissions:
                return LegacyAccessControlRole.ADMIN
            if "dashboards:write" in permissions:
                return LegacyAccessControlRole.EDITOR
            if "dashboards:read" in permissions:
                return LegacyAccessControlRole.VIEWER
            return LegacyAccessControlRole.NONE

        # setup an in-mem ServiceAccountUser
        role = LegacyAccessControlRole.NONE
        if not organization.is_rbac_permissions_enabled:
            role = _determine_role_from_permissions(permissions)

        user = ServiceAccountUser(
            organization=organization,
            service_account=service_account,
            username=service_account.username,
            public_primary_key=service_account.public_primary_key,
            role=role,
            permissions=GrafanaAPIPermissions.construct_permissions(permissions.keys()),
        )

        return user, validated_token
