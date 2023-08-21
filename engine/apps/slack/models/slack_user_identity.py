import logging
import typing

import requests
from django.db import models

from apps.slack.constants import SLACK_BOT_ID
from apps.slack.scenarios.notified_user_not_in_channel import NotifiedUserNotInChannelStep
from apps.slack.slack_client import SlackClientWithErrorHandling
from apps.slack.slack_client.exceptions import SlackAPIException, SlackAPITokenException
from apps.user_management.models import Organization, User

if typing.TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

logger = logging.getLogger(__name__)


class AllSlackUserIdentityManager(models.Manager):
    use_in_migrations = False

    def get_queryset(self):
        return super().get_queryset()


class SlackUserIdentityManager(models.Manager):
    use_in_migrations = False

    def get_queryset(self):
        return super().get_queryset().filter(counter=1)

    def get(self, **kwargs):
        try:
            instance = super().get(**kwargs, is_restricted=False, is_ultra_restricted=False)
        except SlackUserIdentity.DoesNotExist:
            instance = self.filter(**kwargs).first()
            if instance is None:
                raise SlackUserIdentity.DoesNotExist
        return instance


class SlackUserIdentity(models.Model):
    users: "RelatedManager['User']"

    objects: models.Manager["SlackUserIdentity"] = SlackUserIdentityManager()
    all_objects: models.Manager["SlackUserIdentity"] = AllSlackUserIdentityManager()

    id = models.AutoField(primary_key=True)

    slack_id = models.CharField(max_length=100)

    slack_team_identity = models.ForeignKey(
        "SlackTeamIdentity", on_delete=models.PROTECT, related_name="slack_user_identities"
    )

    cached_slack_email = models.EmailField(blank=True, default="")

    cached_im_channel_id = models.CharField(max_length=100, null=True, default=None)
    cached_phone_number = models.CharField(max_length=20, null=True, default=None)
    cached_country_code = models.CharField(max_length=3, null=True, default=None)
    cached_timezone = models.CharField(max_length=100, null=True, default=None)
    cached_slack_login = models.CharField(max_length=100, null=True, default=None)
    cached_avatar = models.URLField(max_length=200, null=True, default=None)
    cached_name = models.CharField(max_length=200, null=True, default=None)

    phone_from_onboarding = models.BooleanField(default=False)

    cached_is_bot = models.BooleanField(null=True, default=None)

    # Fields from user profile
    profile_real_name_normalized = models.CharField(max_length=200, null=True, default=None)
    profile_display_name = models.CharField(max_length=200, null=True, default=None)
    profile_display_name_normalized = models.CharField(max_length=200, null=True, default=None)
    profile_real_name = models.CharField(max_length=200, null=True, default=None)

    deleted = models.BooleanField(null=True, default=None)
    is_admin = models.BooleanField(null=True, default=None)
    is_owner = models.BooleanField(null=True, default=None)
    is_primary_owner = models.BooleanField(null=True, default=None)
    is_restricted = models.BooleanField(null=True, default=None)
    is_ultra_restricted = models.BooleanField(null=True, default=None)
    is_app_user = models.BooleanField(null=True, default=None)
    has_2fa = models.BooleanField(null=True, default=None)

    main_menu_last_opened_datetime = models.DateTimeField(null=True, default=None)
    counter = models.PositiveSmallIntegerField(default=1)

    is_stranger = models.BooleanField(default=False)
    is_not_found = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["slack_id", "slack_team_identity", "counter"], name="unique_slack_identity_per_team"
            )
        ]

    def __str__(self):
        return self.slack_login

    def send_link_to_slack_message(self, slack_message):
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": "You are invited to look at an alert group!",
                    "emoji": True,
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "action_id": f"{NotifiedUserNotInChannelStep.routing_uid()}",
                        "text": {"type": "plain_text", "text": "➡️ Go to the alert group"},
                        "url": slack_message.permalink,
                        "style": "primary",
                    }
                ],
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": (
                            f"You received this message because you're not a member of <#{slack_message.channel_id}>.\n"
                            "Please join the channel to get notified right in the alert group thread."
                        ),
                    }
                ],
            },
        ]

        sc = SlackClientWithErrorHandling(self.slack_team_identity.bot_access_token)
        return sc.api_call(
            "chat.postMessage",
            channel=self.im_channel_id,
            text="You are invited to look at an alert group!",
            blocks=blocks,
        )

    @property
    def slack_verbal(self):
        return (
            self.profile_real_name_normalized
            or self.profile_real_name
            or self.profile_display_name_normalized
            or self.profile_display_name
            or self.cached_name
            or self.cached_slack_login
        )

    @property
    def slack_login(self):
        if self.cached_slack_login is None or self.cached_slack_login == "slack_token_revoked_unable_to_cache_login":
            sc = SlackClientWithErrorHandling(self.slack_team_identity.bot_access_token)
            try:
                result = sc.api_call(
                    "users.info",
                    user=self.slack_id,
                    team=self.slack_team_identity,
                )
                self.cached_slack_login = result["user"]["name"]
                self.save()
            except SlackAPITokenException as e:
                logger.warning("Unable to get slack login: token revoked\n" + str(e))
                self.cached_slack_login = "slack_token_revoked_unable_to_cache_login"
                self.save()
                return "slack_token_revoked_unable_to_cache_login"
            except SlackAPIException as e:
                if e.response["error"] == "user_not_found":
                    logger.warning("user_not_found " + str(e))
                    self.cached_slack_login = "user_not_found"
                    self.save()
                elif e.response["error"] == "invalid_auth":
                    return "no_enough_permissions_to_retrieve"
                else:
                    raise e

        return str(self.cached_slack_login)

    @property
    def timezone(self):
        if self.cached_timezone is None or self.cached_timezone == "None":
            sc = SlackClientWithErrorHandling(self.slack_team_identity.bot_access_token)
            try:
                result = sc.api_call(
                    "users.info",
                    user=self.slack_id,
                    timeout=5,
                )
                tz_from_slack = result["user"].get("tz", "UTC")
                if tz_from_slack == "None" or tz_from_slack is None:
                    tz_from_slack = "UTC"
                self.cached_timezone = tz_from_slack
                self.save(update_fields=["cached_timezone"])
            except SlackAPITokenException as e:
                print("Token revoked: " + str(e))
            except requests.exceptions.Timeout:
                # Do not save tz in case of timeout to try to load it later again
                return "UTC"

        return str(self.cached_timezone)

    @property
    def im_channel_id(self):
        if self.cached_im_channel_id is None:
            sc = SlackClientWithErrorHandling(self.slack_team_identity.bot_access_token)
            try:
                result = sc.api_call("conversations.open", users=self.slack_id, return_im=True)
                self.cached_im_channel_id = result["channel"]["id"]
                self.save()
            except SlackAPIException as e:
                if e.response["error"] == "cannot_dm_bot":
                    logger.warning("Trying to DM bot " + str(e))
                else:
                    raise e

        return self.cached_im_channel_id

    def update_profile_info(self):
        sc = SlackClientWithErrorHandling(self.slack_team_identity.bot_access_token)
        logger.info("Update user profile info")
        try:
            result = sc.api_call(
                "users.info",
                user=self.slack_id,
                team=self.slack_team_identity,
            )
        except SlackAPITokenException as e:
            logger.warning(f"Unable to get user info due token revoked or account inactive: {e}")
            result = None
        else:
            if not self.cached_slack_email and "email" in result["user"]["profile"]:
                self.cached_slack_email = result["user"]["profile"]["email"]
            if "real_name" in result["user"]["profile"]:
                self.profile_real_name = result["user"]["profile"]["real_name"]
            if "real_name_normalized" in result["user"]["profile"]:
                self.profile_real_name_normalized = result["user"]["profile"]["real_name_normalized"]
            if "display_name" in result["user"]["profile"]:
                self.profile_display_name = result["user"]["profile"]["display_name"]
            if "display_name_normalized" in result["user"]["profile"]:
                self.profile_display_name_normalized = result["user"]["profile"]["display_name_normalized"]
            self.cached_avatar = result["user"]["profile"].get("image_512")
            if result["user"].get("is_bot") is True or result["user"].get("id") == SLACK_BOT_ID:
                self.cached_is_bot = True
            self.cached_name = result["user"].get("real_name", result["user"]["name"])
            self.cached_slack_login = result["user"].get("name")
            self.save()
        return result

    def get_slack_username(self):
        if not self.slack_verbal:
            logger.info("Trying to get username from slack")
            result = self.update_profile_info()
            if result is None:
                logger.info("Unable to populate username")
                return None
        return self.slack_verbal or self.cached_slack_email.split("@")[0] or None

    def get_user(self, organization: Organization) -> User | None:
        try:
            user = organization.users.get(slack_user_identity=self)
        except User.DoesNotExist:
            user = None
        return user
