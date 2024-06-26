from typing import Tuple

from django.db import models

from apps.auth_token import constants, crypto
from apps.auth_token.models import BaseAuthToken
from apps.user_management.models import Organization, User


class MattermostAuthToken(BaseAuthToken):
    objects: models.Manager["MattermostAuthToken"]

    user = models.ForeignKey(
        "user_management.User",
        related_name="mattermost_auth_token_set",
        on_delete=models.CASCADE,
    )

    organization = models.OneToOneField(
        "user_management.Organization", on_delete=models.CASCADE, related_name="mattermost_auth_token"
    )

    @classmethod
    def create_auth_token(cls, user: User, organization: Organization) -> Tuple["MattermostAuthToken", str]:
        token_string = crypto.generate_token_string()
        digest = crypto.hash_token_string(token_string)

        instance = cls.objects.create(
            token_key=token_string[: constants.TOKEN_KEY_LENGTH],
            digest=digest,
            user=user,
            organization=organization,
        )
        return instance, token_string
