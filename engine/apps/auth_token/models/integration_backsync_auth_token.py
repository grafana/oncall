from typing import Tuple

from django.db import models

from apps.alerts.models import AlertReceiveChannel
from apps.auth_token import constants, crypto
from apps.auth_token.models import BaseAuthToken
from apps.user_management.models import Organization


class IntegrationBacksyncAuthToken(BaseAuthToken):
    alert_receive_channel = models.ForeignKey(
        "alerts.AlertReceiveChannel",
        on_delete=models.CASCADE,
        related_name="auth_tokens",
    )
    organization = models.ForeignKey(
        "user_management.Organization", related_name="integration_auth_tokens", on_delete=models.CASCADE
    )

    @classmethod
    def create_auth_token(
        cls,
        alert_receive_channel: AlertReceiveChannel,
        organization: Organization,
    ) -> Tuple["IntegrationBacksyncAuthToken", str]:
        old_token = cls.objects.filter(alert_receive_channel=alert_receive_channel)
        if old_token.exists():
            old_token.delete()

        token_string = crypto.generate_token_string()
        digest = crypto.hash_token_string(token_string)

        instance = cls.objects.create(
            token_key=token_string[: constants.TOKEN_KEY_LENGTH],
            digest=digest,
            alert_receive_channel=alert_receive_channel,
            organization=organization,
        )
        return instance, token_string
