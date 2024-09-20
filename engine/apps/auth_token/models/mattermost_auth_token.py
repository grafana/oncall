from typing import Tuple

from django.db import models
from django.utils import timezone

from apps.auth_token import constants, crypto
from apps.auth_token.models import BaseAuthToken
from apps.user_management.models import Organization, User
from settings.base import AUTH_TOKEN_TIMEOUT_SECONDS


def get_expire_date():
    return timezone.now() + timezone.timedelta(seconds=AUTH_TOKEN_TIMEOUT_SECONDS)


class MattermostAuthToken(BaseAuthToken):
    user = models.OneToOneField("user_management.User", related_name="mattermost_auth_token", on_delete=models.CASCADE)
    organization = models.ForeignKey(
        "user_management.Organization", related_name="mattermost_auth_token_set", on_delete=models.CASCADE
    )
    expire_date = models.DateTimeField(default=get_expire_date)

    @classmethod
    def create_auth_token(cls, user: User, organization: Organization) -> Tuple["MattermostAuthToken", str]:
        old_token = cls.objects_with_deleted.filter(user=user)
        if old_token.exists():
            old_token.delete()

        token_string = crypto.generate_token_string()
        digest = crypto.hash_token_string(token_string)

        instance = cls.objects.create(
            token_key=token_string[: constants.TOKEN_KEY_LENGTH],
            digest=digest,
            user=user,
            organization=organization,
        )
        return instance, token_string
