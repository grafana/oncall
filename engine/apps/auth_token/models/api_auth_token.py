from typing import Tuple

from django.db import models

from apps.auth_token import constants, crypto
from apps.auth_token.models.base_auth_token import BaseAuthToken
from apps.user_management.models import Organization, User


class ApiAuthToken(BaseAuthToken):
    objects: models.QuerySet["ApiAuthToken"]

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
        return instance, token_string

    # Insight logs
    @property
    def insight_logs_type_verbal(self):
        return "public_api_token"

    @property
    def insight_logs_verbal(self):
        return self.name

    @property
    def insight_logs_serialized(self):
        # API tokens are not modifiable, so return empty dict to implement InsightLoggable interface
        return {}

    @property
    def insight_logs_metadata(self):
        return {}
