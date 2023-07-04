from typing import Tuple

from django.db import models

from apps.auth_token import constants, crypto
from apps.auth_token.models.base_auth_token import BaseAuthToken
from apps.user_management.models import Organization, User


class UserScheduleExportAuthToken(BaseAuthToken):
    objects: models.Manager["UserScheduleExportAuthToken"]

    class Meta:
        unique_together = ("user", "organization")

    user = models.ForeignKey(
        to=User, null=False, blank=False, related_name="user_schedule_export_token", on_delete=models.CASCADE
    )
    organization = models.ForeignKey(
        to=Organization, null=False, blank=False, related_name="user_schedule_export_token", on_delete=models.CASCADE
    )
    active = models.BooleanField(default=True)

    @classmethod
    def create_auth_token(cls, user: User, organization: Organization) -> Tuple["UserScheduleExportAuthToken", str]:
        token_string = crypto.generate_schedule_token_string()
        digest = crypto.hash_token_string(token_string)

        instance = cls.objects.create(
            token_key=token_string[: constants.TOKEN_KEY_LENGTH],
            digest=digest,
            user=user,
            organization=organization,
        )
        return instance, token_string

    # Insight logs
    @property
    def insight_logs_type_verbal(self):
        return "user_schedule_export_token"

    @property
    def insight_logs_verbal(self):
        return f"Users chedule export token for {self.user.username}"

    @property
    def insight_logs_serialized(self):
        # Schedule export tokens are not modifiable, return empty dict to implement InsightLoggable interface
        return {}

    @property
    def insight_logs_metadata(self):
        return {}
