import logging
import typing

import requests
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import JSONField
from django.utils import timezone

from apps.api.permissions import RBACPermission
from apps.slack.client import SlackClient
from apps.slack.errors import (
    SlackAPIError,
    SlackAPIInvalidUsersError,
    SlackAPIPermissionDeniedError,
    SlackAPITokenError,
    SlackAPIUsergroupNotFoundError,
)
from apps.slack.models import SlackTeamIdentity
from apps.user_management.models.user import User
from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length

if typing.TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

    from apps.alerts.models import EscalationPolicy
    from apps.schedules.models import OnCallSchedule


logger = logging.getLogger(__name__)


def generate_public_primary_key_for_slack_user_group():
    prefix = "G"
    new_public_primary_key = generate_public_primary_key(prefix)

    failure_counter = 0
    while SlackUserGroup.objects.filter(public_primary_key=new_public_primary_key).exists():
        new_public_primary_key = increase_public_primary_key_length(
            failure_counter=failure_counter, prefix=prefix, model_name="SlackUserGroup"
        )
        failure_counter += 1

    return new_public_primary_key


class SlackUserGroup(models.Model):
    escalation_policies: "RelatedManager['EscalationPolicy']"
    oncall_schedules: "RelatedManager['OnCallSchedule']"

    public_primary_key = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH + 1)],
        unique=True,
        default=generate_public_primary_key_for_slack_user_group,
    )

    slack_id = models.CharField(max_length=100)

    slack_team_identity = models.ForeignKey(
        "slack.SlackTeamIdentity",
        on_delete=models.PROTECT,
        related_name="usergroups",
        null=True,
        default=None,
    )
    name = models.CharField(max_length=500)
    handle = models.CharField(max_length=500)
    members = JSONField(default=None, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    last_populated = models.DateField(null=True, default=None)

    class Meta:
        unique_together = ("slack_id", "slack_team_identity")

    @property
    def can_be_updated(self) -> bool:
        sc = SlackClient(self.slack_team_identity, timeout=5)

        try:
            sc.usergroups_update(usergroup=self.slack_id)
            return True
        except (SlackAPIError, requests.exceptions.Timeout):
            return False

    @property
    def oncall_slack_user_identities(self):
        users = set(user for schedule in self.oncall_schedules.get_oncall_users().values() for user in schedule)
        slack_user_identities = []
        for user in users:
            if user.slack_user_identity is not None:
                slack_user_identities.append(user.slack_user_identity)
            else:
                logger.warning(f"User {user.pk} does not have a Slack account connected")

        return slack_user_identities

    def update_oncall_members(self):
        slack_ids = [slack_user_identity.slack_id for slack_user_identity in self.oncall_slack_user_identities]
        logger.info(f"Updating usergroup {self.slack_id}, members {slack_ids}")

        # Slack doesn't allow user groups to be empty
        if len(slack_ids) == 0:
            logger.info(f"Skipping usergroup {self.slack_id}, the list of members is empty")
            return

        # Do not send requests to Slack API in case user group is populated correctly already
        if self.members is not None and set(self.members) == set(slack_ids):
            logger.info(f"Skipping usergroup {self.slack_id}, already populated correctly")
            return

        logger.info(f"Slack user group  {self.slack_id} memberlist in not up-to-date, updating, members {slack_ids}")

        try:
            self.update_members(slack_ids)
        except SlackAPIPermissionDeniedError:
            pass

    def update_members(self, slack_ids):
        sc = SlackClient(self.slack_team_identity, enable_ratelimit_retry=True)

        try:
            sc.usergroups_users_update(usergroup=self.slack_id, users=slack_ids)
        except (SlackAPITokenError, SlackAPIUsergroupNotFoundError, SlackAPIInvalidUsersError) as err:
            logger.warning(f"Slack usergroup {self.slack_id} update failed: {err}")
        except SlackAPIError as slack_api_error:
            logger.warning(f"Slack usergroup {self.slack_id} update failed: {slack_api_error}")
            raise
        else:
            self.members = slack_ids
            self.save(update_fields=("members",))
            logger.info(f"Saved cached memberlist for slack user group {self.slack_id}, members {slack_ids}")

    def get_users_from_members_for_organization(self, organization):
        return organization.users.filter(
            slack_user_identity__slack_id__in=self.members,
            **User.build_permissions_query(RBACPermission.Permissions.CHATOPS_WRITE, organization),
        )

    @classmethod
    def update_or_create_slack_usergroup_from_slack(cls, slack_id: str, slack_team_identity: SlackTeamIdentity) -> None:
        sc = SlackClient(slack_team_identity)
        usergroups = sc.usergroups_list()["usergroups"]

        try:
            usergroup = [ug for ug in usergroups if ug["id"] == slack_id][0]
        except IndexError:
            # user group not found
            return

        try:
            members = sc.usergroups_users_list(usergroup=usergroup["id"])["users"]
        except SlackAPIError:
            return

        SlackUserGroup.objects.update_or_create(
            slack_id=usergroup["id"],
            slack_team_identity=slack_team_identity,
            defaults={
                "name": usergroup["name"],
                "handle": usergroup["handle"],
                "members": members,
                "is_active": usergroup["date_delete"] == 0,
                "last_populated": timezone.now().date(),
            },
        )
