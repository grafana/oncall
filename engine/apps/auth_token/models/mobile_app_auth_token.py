from typing import Tuple

from django.db import models

from apps.auth_token import constants, crypto
from apps.auth_token.models.base_auth_token import BaseAuthToken
from apps.user_management.models import Organization, User


class MobileAppAuthToken(BaseAuthToken):
    user = models.ForeignKey(
        to=User, null=False, blank=False, related_name="mobile_app_auth_tokens", on_delete=models.CASCADE
    )
    organization = models.ForeignKey(
        to=Organization, null=False, blank=False, related_name="mobile_app_auth_tokens", on_delete=models.CASCADE
    )

    @classmethod
    def create_auth_token(cls, user: User, organization: Organization) -> Tuple["MobileAppAuthToken", str]:
        token_string = crypto.generate_token_string()
        digest = crypto.hash_token_string(token_string)

        instance = cls.objects.create(
            token_key=token_string[: constants.TOKEN_KEY_LENGTH],
            digest=digest,
            user=user,
            organization=organization,
        )
        return instance, token_string
