from typing import Tuple

from django.db import models

from apps.auth_token import constants, crypto
from apps.auth_token.models.base_auth_token import BaseAuthToken
from apps.schedules.models import OnCallSchedule
from apps.user_management.models import Organization, User
from apps.user_management.organization_log_creator import OrganizationLogType, create_organization_log


class ScheduleExportAuthToken(BaseAuthToken):
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
        cls, user: User, organization: Organization, schedule: OnCallSchedule = None
    ) -> Tuple["ScheduleExportAuthToken", str]:
        token_string = crypto.generate_schedule_token_string()
        digest = crypto.hash_token_string(token_string)

        instance = cls.objects.create(
            token_key=token_string[: constants.TOKEN_KEY_LENGTH],
            digest=digest,
            user=user,
            organization=organization,
            schedule=schedule,
        )
        description = "Schedule export token was created by user {0} for schedule {1}".format(
            user.username, schedule.name
        )
        create_organization_log(organization, user, OrganizationLogType.TYPE_SCHEDULE_EXPORT_TOKEN_CREATED, description)
        return instance, token_string
