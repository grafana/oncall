import binascii
from hmac import compare_digest
from typing import Optional

from django.db import models
from django.utils import timezone

from apps.auth_token import constants
from apps.auth_token.crypto import hash_token_string
from apps.auth_token.exceptions import InvalidToken


class AuthTokenQueryset(models.QuerySet):
    def filter(self, *args, **kwargs):
        return super().filter(*args, **kwargs, revoked_at=None)

    def delete(self):
        self.update(revoked_at=timezone.now())


class BaseAuthToken(models.Model):
    class Meta:
        abstract = True

    objects = AuthTokenQueryset.as_manager()
    objects_with_deleted = models.Manager()

    token_key = models.CharField(max_length=constants.TOKEN_KEY_LENGTH, db_index=True)
    digest = models.CharField(max_length=constants.DIGEST_LENGTH)

    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True)

    @classmethod
    def validate_token_string(cls, token: str, *args, **kwargs) -> Optional["BaseAuthToken"]:
        for auth_token in cls.objects.filter(token_key=token[: constants.TOKEN_KEY_LENGTH]):
            try:
                digest = hash_token_string(token)
            except (TypeError, binascii.Error):
                raise InvalidToken
            if compare_digest(digest, auth_token.digest):
                return auth_token

        raise InvalidToken
