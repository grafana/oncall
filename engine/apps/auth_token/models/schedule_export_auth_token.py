import typing

from django.db import models

from apps.auth_token import constants, crypto
from apps.auth_token.models.base_auth_token import BaseAuthToken
from apps.schedules.models import OnCallSchedule
from apps.user_management.models import Organization, User


class ScheduleExportAuthToken(BaseAuthToken):
    objects: models.Manager["ScheduleExportAuthToken"]

    class Meta:
        unique_together = ("user", "organization", "schedule")

    user = models.ForeignKey(
        to=User, null=False, blank=False, related_name="schedule_export_token", on_delete=models.CASCADE
    )
    organization = models.ForeignKey(
        to=Organization, null=False, blank=False, related_name="schedule_export_token", on_delete=models.CASCADE
    )
    schedule = models.ForeignKey(
        to=OnCallSchedule, null=True, blank=True, related_name="schedule_export_token", on_delete=models.CASCADE
    )
    active = models.BooleanField(default=True)

    @classmethod
    def create_auth_token(
        cls, user: User, organization: Organization, schedule: typing.Optional[OnCallSchedule] = None
    ) -> typing.Tuple["ScheduleExportAuthToken", str]:
        token_string = crypto.generate_schedule_token_string()
        digest = crypto.hash_token_string(token_string)

        instance = cls.objects.create(
            token_key=token_string[: constants.TOKEN_KEY_LENGTH],
            digest=digest,
            user=user,
            organization=organization,
            schedule=schedule,
        )
        return instance, token_string

    # Insight logs
    @property
    def insight_logs_type_verbal(self):
        return "schedule_export_token"

    @property
    def insight_logs_verbal(self):
        return f"Schedule export token for {self.schedule.insight_logs_verbal}"

    @property
    def insight_logs_serialized(self):
        # Schedule export tokens are not modifiable, return empty dict to implement InsightLoggable interface
        return {}

    @property
    def insight_logs_metadata(self):
        return {}
