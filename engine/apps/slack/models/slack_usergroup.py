import logging
import typing

import requests
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import JSONField
from django.utils import timezone

from apps.api.permissions import RBACPermission
from apps.slack.slack_client import SlackClientWithErrorHandling
from apps.slack.slack_client.exceptions import SlackAPIException
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
        sc = SlackClientWithErrorHandling(self.slack_team_identity.bot_access_token)

        try:
            sc.api_call("usergroups.update", usergroup=self.slack_id, timeout=5)
            return True
        except (SlackAPIException, requests.exceptions.Timeout):
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

        try:
            self.update_members(slack_ids)
        except SlackAPIException as e:
            if e.response["error"] == "permission_denied":
                logger.warning(f"Could not update usergroup {self.slack_id} due to permission_denied")

    def update_members(self, slack_ids):
        sc = SlackClientWithErrorHandling(self.slack_team_identity.bot_access_token)

        sc.api_call(
            "usergroups.users.update",
            usergroup=self.slack_id,
            users=slack_ids,
        )

        self.members = slack_ids
        self.save(update_fields=("members",))

    def get_users_from_members_for_organization(self, organization):
        return organization.users.filter(
            slack_user_identity__slack_id__in=self.members,
            **User.build_permissions_query(RBACPermission.Permissions.CHATOPS_WRITE, organization),
        )

    @classmethod
    def update_or_create_slack_usergroup_from_slack(cls, slack_id, slack_team_identity):
        sc = SlackClientWithErrorHandling(slack_team_identity.bot_access_token)
        bot_access_token_accepted = True
        try:
            usergroups_list = sc.api_call(
                "usergroups.list",
            )
        except SlackAPIException as e:
            if e.response["error"] == "not_allowed_token_type":
                # Trying same request with access token. It is required due to migration to granular permissions
                # and can be removed after clients reinstall their bots
                try:
                    sc_with_access_token = SlackClientWithErrorHandling(slack_team_identity.access_token)
                    usergroups_list = sc_with_access_token.api_call(
                        "usergroups.list",
                    )
                    bot_access_token_accepted = False
                except SlackAPIException as err:
                    if err.response["error"] == "missing_scope":
                        return None, False
                    else:
                        raise err
            elif e.response["error"] == "missing_scope":
                return None, False
            else:
                raise e

        for usergroup in usergroups_list["usergroups"]:
            if usergroup["id"] == slack_id:
                try:
                    if bot_access_token_accepted:
                        usergroups_users = sc.api_call(
                            "usergroups.users.list",
                            usergroup=usergroup["id"],
                        )
                    else:
                        sc_with_access_token = SlackClientWithErrorHandling(slack_team_identity.access_token)
                        usergroups_users = sc_with_access_token.api_call(
                            "usergroups.users.list",
                            usergroup=usergroup["id"],
                        )
                except SlackAPIException as e:
                    if e.response["error"] == "no_such_subteam":
                        logger.info("User group does not exist")
                    else:
                        logger.error(
                            f"'usergroups.users.list' slack api error. "
                            f"SlackTeamIdentity pk: {slack_team_identity.pk}\n{e}"
                        )
                else:
                    usergroup_name = usergroup["name"]
                    usergroup_handle = usergroup["handle"]
                    usergroup_members = usergroups_users["users"]
                    usergroup_is_active = usergroup["date_delete"] == 0

                    return SlackUserGroup.objects.update_or_create(
                        slack_id=usergroup["id"],
                        slack_team_identity=slack_team_identity,
                        defaults={
                            "name": usergroup_name,
                            "handle": usergroup_handle,
                            "members": usergroup_members,
                            "is_active": usergroup_is_active,
                            "last_populated": timezone.now().date(),
                        },
                    )
