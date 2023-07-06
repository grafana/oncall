import binascii
from hmac import compare_digest
from typing import Tuple

from django.db import models

from apps.auth_token import constants
from apps.auth_token.crypto import (
    generate_plugin_token_string,
    generate_plugin_token_string_and_salt,
    hash_token_string,
)
from apps.auth_token.exceptions import InvalidToken
from apps.auth_token.models import BaseAuthToken
from apps.user_management.models import Organization


class PluginAuthToken(BaseAuthToken):
    objects: models.Manager["PluginAuthToken"]

    salt = models.CharField(max_length=constants.AUTH_TOKEN_CHARACTER_LENGTH, null=True)
    organization = models.ForeignKey(
        to=Organization,
        on_delete=models.CASCADE,
        related_name="plugin_auth_tokens",
    )

    @classmethod
    def create_auth_token(cls, organization: Organization) -> Tuple["PluginAuthToken", str]:
        old_token = cls.objects.filter(organization=organization)

        if old_token.exists():
            old_token.delete()

        token_string, salt = generate_plugin_token_string_and_salt(organization.stack_id, organization.org_id)
        digest = hash_token_string(token_string)

        auth_token = cls.objects.create(
            token_key=token_string[: constants.TOKEN_KEY_LENGTH],
            digest=digest,
            salt=salt,
            organization=organization,
        )
        return auth_token, token_string

    @classmethod
    def validate_token_string(cls, token: str, *args, **kwargs) -> "PluginAuthToken":
        context = kwargs["context"]
        for auth_token in cls.objects.filter(token_key=token[: constants.TOKEN_KEY_LENGTH]):
            try:
                stack_id = int(context["stack_id"])
                org_id = int(context["org_id"])
                salt = binascii.unhexlify(auth_token.salt)
                recreated_token = generate_plugin_token_string(salt, stack_id, org_id)
                digest = hash_token_string(recreated_token)
            except (TypeError, binascii.Error):
                raise InvalidToken
            if compare_digest(digest, auth_token.digest) and token == recreated_token:
                return auth_token

        raise InvalidToken
