import logging
import typing

from django.db import models
from django.db.models import JSONField

from apps.api.permissions import RBACPermission
from apps.slack.constants import SLACK_INVALID_AUTH_RESPONSE, SLACK_WRONG_TEAM_NAMES
from apps.slack.slack_client import SlackClientWithErrorHandling
from apps.slack.slack_client.exceptions import SlackAPIException, SlackAPITokenException
from apps.user_management.models.user import User
from common.insight_log.chatops_insight_logs import ChatOpsEvent, ChatOpsTypePlug, write_chatops_insight_log

if typing.TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

    from apps.user_management.models import Organization

logger = logging.getLogger(__name__)


class SlackTeamIdentity(models.Model):
    organizations: "RelatedManager['Organization']"

    id = models.AutoField(primary_key=True)
    slack_id = models.CharField(max_length=100)
    cached_name = models.CharField(max_length=100, null=True, default=None)
    cached_app_id = models.CharField(max_length=100, null=True, default=None)
    access_token = models.CharField(max_length=100, null=True, default=None)
    bot_user_id = models.CharField(max_length=100, null=True, default=None)
    bot_access_token = models.CharField(max_length=100, null=True, default=None)
    oauth_scope = models.TextField(max_length=30000, null=True, default=None)
    detected_token_revoked = models.DateTimeField(null=True, default=None, verbose_name="Deleted At")
    is_profile_populated = models.BooleanField(default=False)
    datetime = models.DateTimeField(auto_now_add=True)
    installed_via_granular_permissions = models.BooleanField(default=True)

    installed_by = models.ForeignKey("SlackUserIdentity", on_delete=models.PROTECT, null=True, default=None)

    last_populated = models.DateTimeField(null=True, default=None)

    cached_bot_id = models.CharField(max_length=100, null=True, default=None)

    # response after oauth.access. This field is used to reinstall app to another OnCall workspace
    cached_reinstall_data = JSONField(null=True, default=None)

    class Meta:
        ordering = ("datetime",)

    def __str__(self):
        return f"{self.pk}: {self.name}"

    def update_oauth_fields(self, user, organization, reinstall_data):
        logger.info(f"updated oauth_fields for sti {self.pk}")
        from apps.slack.models import SlackUserIdentity

        organization.slack_team_identity = self
        organization.save(update_fields=["slack_team_identity"])
        slack_user_identity, _ = SlackUserIdentity.objects.get_or_create(
            slack_id=reinstall_data["authed_user"]["id"],
            slack_team_identity=self,
        )
        user.slack_user_identity = slack_user_identity
        user.save(update_fields=["slack_user_identity"])
        self.bot_access_token = reinstall_data["access_token"]
        self.bot_user_id = reinstall_data["bot_user_id"]
        self.oauth_scope = reinstall_data["scope"]
        self.cached_name = reinstall_data["team"]["name"]
        self.access_token = reinstall_data["authed_user"]["access_token"]
        self.installed_by = slack_user_identity
        self.cached_reinstall_data = None
        self.installed_via_granular_permissions = True
        self.save()
        write_chatops_insight_log(
            author=user, event_name=ChatOpsEvent.WORKSPACE_CONNECTED, chatops_type=ChatOpsTypePlug.SLACK.value
        )

    def get_cached_channels(self, search_term=None, slack_id=None):
        queryset = self.cached_channels
        if search_term is not None:
            queryset = queryset.filter(name__startswith=search_term)
        if slack_id is not None:
            queryset = queryset.filter(slack_id=slack_id)
        return queryset.all()

    @property
    def bot_id(self):
        if self.cached_bot_id is None:
            sc = SlackClientWithErrorHandling(self.bot_access_token)
            auth = sc.api_call("auth.test")
            self.cached_bot_id = auth.get("bot_id")
            self.save(update_fields=["cached_bot_id"])
        return self.cached_bot_id

    @property
    def members(self):
        sc = SlackClientWithErrorHandling(self.bot_access_token)

        next_cursor = None
        members = []
        while next_cursor != "" or next_cursor is None:
            result = sc.api_call("users.list", cursor=next_cursor, team=self)
            next_cursor = result["response_metadata"]["next_cursor"]
            members += result["members"]

        return members

    @property
    def name(self):
        if self.cached_name is None or self.cached_name in SLACK_WRONG_TEAM_NAMES:
            try:
                sc = SlackClientWithErrorHandling(self.bot_access_token)
                result = sc.api_call("team.info")
                self.cached_name = result["team"]["name"]
                self.save()
            except SlackAPIException as e:
                if e.response["error"] == "invalid_auth":
                    self.cached_name = SLACK_INVALID_AUTH_RESPONSE
                    self.save()
                else:
                    raise e
        return self.cached_name

    @property
    def app_id(self):
        if not self.cached_app_id:
            sc = SlackClientWithErrorHandling(self.bot_access_token)
            result = sc.api_call("bots.info", bot=self.bot_id)
            app_id = result["bot"]["app_id"]
            self.cached_app_id = app_id
            self.save(update_fields=["cached_app_id"])
        return self.cached_app_id

    def get_users_from_slack_conversation_for_organization(self, channel_id, organization):
        sc = SlackClientWithErrorHandling(self.bot_access_token)
        members = self.get_conversation_members(sc, channel_id)

        return organization.users.filter(
            slack_user_identity__slack_id__in=members,
            **User.build_permissions_query(RBACPermission.Permissions.CHATOPS_WRITE, organization),
        )

    def get_conversation_members(self, slack_client, channel_id):
        try:
            members = slack_client.paginated_api_call(
                "conversations.members", channel=channel_id, paginated_key="members"
            )["members"]
        except SlackAPITokenException as e:
            logger.warning(
                f"Unable to get members from slack conversation for Slack team identity pk: {self.pk}.\n" f"{e}"
            )
            members = []
        except SlackAPIException as e:
            if e.response["error"] == "fetch_members_failed":
                logger.warning(
                    f"Unable to get members from slack conversation: 'fetch_members_failed'. "
                    f"Slack team identity pk: {self.pk}.\n"
                    f"{e}"
                )
                members = []
            elif e.response["error"] == "channel_not_found":
                logger.warning(
                    f"Unable to get members from slack conversation: 'channel_not_found'. "
                    f"Slack team identity pk: {self.pk}.\n"
                    f"{e}"
                )
                members = []
            else:
                raise e

        return members
