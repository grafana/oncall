import logging
import typing

from django.db import models
from django.db.models import JSONField

from apps.api.permissions import RBACPermission
from apps.slack.client import SlackClient
from apps.slack.constants import SLACK_INVALID_AUTH_RESPONSE, SLACK_WRONG_TEAM_NAMES
from apps.slack.errors import (
    SlackAPIChannelNotFoundError,
    SlackAPIFetchMembersFailedError,
    SlackAPIInvalidAuthError,
    SlackAPITokenError,
)
from apps.user_management.models.user import User

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
    access_token = models.CharField(max_length=255, null=True, default=None)
    bot_user_id = models.CharField(max_length=100, null=True, default=None)
    bot_access_token = models.CharField(max_length=255, null=True, default=None)
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

    def update_oauth_fields(self, user, organization, oauth_response):
        logger.info(f"updated oauth_fields for sti {self.pk}")
        from apps.slack.models import SlackUserIdentity

        organization.slack_team_identity = self
        organization.save(update_fields=["slack_team_identity"])
        slack_user_identity, _ = SlackUserIdentity.objects.get_or_create(
            slack_id=oauth_response["authed_user"]["id"],
            slack_team_identity=self,
        )
        user.slack_user_identity = slack_user_identity
        user.save(update_fields=["slack_user_identity"])
        self.bot_access_token = oauth_response["access_token"]
        self.bot_user_id = oauth_response["bot_user_id"]
        self.oauth_scope = oauth_response["scope"]
        self.cached_name = oauth_response["team"]["name"]
        self.access_token = oauth_response["authed_user"]["access_token"]
        self.installed_by = slack_user_identity
        self.cached_reinstall_data = None
        self.installed_via_granular_permissions = True
        self.save()

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
            sc = SlackClient(self)
            auth = sc.auth_test()
            self.cached_bot_id = auth.get("bot_id")
            self.save(update_fields=["cached_bot_id"])
        return self.cached_bot_id

    @property
    def members(self):
        sc = SlackClient(self)

        next_cursor = None
        members = []
        while next_cursor != "" or next_cursor is None:
            result = sc.users_list(cursor=next_cursor, team=self)
            next_cursor = result["response_metadata"]["next_cursor"]
            members += result["members"]

        return members

    @property
    def name(self):
        if self.cached_name is None or self.cached_name in SLACK_WRONG_TEAM_NAMES:
            try:
                sc = SlackClient(self)
                result = sc.team_info()
                self.cached_name = result["team"]["name"]
                self.save()
            except SlackAPIInvalidAuthError:
                self.cached_name = SLACK_INVALID_AUTH_RESPONSE
                self.save()
        return self.cached_name

    @property
    def app_id(self):
        if not self.cached_app_id:
            sc = SlackClient(self)
            result = sc.bots_info(bot=self.bot_id)
            app_id = result["bot"]["app_id"]
            self.cached_app_id = app_id
            self.save(update_fields=["cached_app_id"])
        return self.cached_app_id

    def get_users_from_slack_conversation_for_organization(self, channel_id, organization):
        sc = SlackClient(self)
        members = self.get_conversation_members(sc, channel_id)

        return organization.users.filter(
            slack_user_identity__slack_id__in=members,
            **User.build_permissions_query(RBACPermission.Permissions.CHATOPS_WRITE, organization),
        )

    def get_conversation_members(self, slack_client: SlackClient, channel_id: str):
        try:
            return slack_client.paginated_api_call(
                "conversations_members", paginated_key="members", channel=channel_id
            )["members"]
        except (SlackAPITokenError, SlackAPIFetchMembersFailedError, SlackAPIChannelNotFoundError):
            return []
