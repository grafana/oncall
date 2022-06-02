from typing import Tuple

from django.db import models

from apps.auth_token import constants, crypto
from apps.auth_token.models.base_auth_token import BaseAuthToken
from apps.user_management.models import Organization, User
from apps.user_management.organization_log_creator import OrganizationLogType, create_organization_log


class ApiAuthToken(BaseAuthToken):
    user = models.ForeignKey(to=User, null=False, blank=False, related_name="auth_tokens", on_delete=models.CASCADE)
    organization = models.ForeignKey(
        to=Organization, null=False, blank=False, related_name="auth_tokens", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=50)

    @classmethod
    def create_auth_token(cls, user: User, organization: Organization, name: str) -> Tuple["ApiAuthToken", str]:
        token_string = crypto.generate_token_string()
        digest = crypto.hash_token_string(token_string)

        instance = cls.objects.create(
            token_key=token_string[: constants.TOKEN_KEY_LENGTH],
            digest=digest,
            user=user,
            organization=organization,
            name=name,
        )
        description = f"API token {instance.name} was created"
        create_organization_log(organization, user, OrganizationLogType.TYPE_API_TOKEN_CREATED, description)
        return instance, token_string
