from typing import Tuple

from django.db import models
from django.utils import timezone

from apps.auth_token import constants, crypto
from apps.auth_token.models import BaseAuthToken
from apps.user_management.models import Organization, User
from settings.base import SLACK_AUTH_TOKEN_TIMEOUT_SECONDS


def get_expire_date():
    return timezone.now() + timezone.timedelta(seconds=SLACK_AUTH_TOKEN_TIMEOUT_SECONDS)


class SlackAuthTokenQueryset(models.QuerySet):
    def filter(self, *args, **kwargs):
        now = timezone.now()
        return super().filter(*args, **kwargs, revoked_at=None, expire_date__gte=now)

    def delete(self):
        self.update(revoked_at=timezone.now())


class SlackAuthToken(BaseAuthToken):
    objects = SlackAuthTokenQueryset.as_manager()
    user = models.ForeignKey(
        "user_management.User",
        related_name="slack_auth_token_set",
        on_delete=models.CASCADE,
    )
    organization = models.ForeignKey(
        "user_management.Organization", related_name="slack_auth_token_set", on_delete=models.CASCADE
    )
    expire_date = models.DateTimeField(default=get_expire_date)

    @classmethod
    def create_auth_token(cls, user: User, organization: Organization) -> Tuple["SlackAuthToken", str]:
        token_string = crypto.generate_token_string()
        digest = crypto.hash_token_string(token_string)

        instance = cls.objects.create(
            token_key=token_string[: constants.TOKEN_KEY_LENGTH],
            digest=digest,
            user=user,
            organization=organization,
        )
        return instance, token_string
