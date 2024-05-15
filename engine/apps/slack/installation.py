import logging

from apps.slack.tasks import (
    clean_slack_integration_leftovers,
    populate_slack_channels_for_team,
    populate_slack_usergroups_for_team,
    unpopulate_slack_user_identities,
)
from common.insight_log import ChatOpsEvent, ChatOpsTypePlug, write_chatops_insight_log

logger = logging.getLogger(__name__)


class SlackInstallationExc(Exception):
    """
    SlackInstallationExc represents some exception happened while installing Slack integration.
    """

    def __init__(self, error_message=None):
        # error message is a user-visible error message
        self.error_message = error_message


def install_slack_integration(organization, user, oauth_response):
    from apps.slack.models import SlackTeamIdentity

    if organization.slack_team_identity is not None:
        # means that organization already has Slack integration
        raise SlackInstallationExc("Failed to install Slack integration: Organization already has Slack integration")

    slack_team_id = oauth_response["team"]["id"]
    slack_team_identity, is_slack_team_identity_created = SlackTeamIdentity.objects.get_or_create(
        slack_id=slack_team_id,
    )
    # update slack oauth fields by data from response
    slack_team_identity.update_oauth_fields(user, organization, oauth_response)
    write_chatops_insight_log(
        author=user, event_name=ChatOpsEvent.WORKSPACE_CONNECTED, chatops_type=ChatOpsTypePlug.SLACK.value
    )
    populate_slack_channels_for_team.apply_async((slack_team_identity.pk,))
    user.slack_user_identity.update_profile_info()
    # todo slack: do we need update info for all existing slack users in slack team?
    # 24.03.2024 - this todo here for a while. populate_slack_user_identities automatically links users to slack.
    # Should be useful if we want to unify with Incident.
    # populate_slack_user_identities.apply_async((organization.pk,))
    populate_slack_usergroups_for_team.apply_async((slack_team_identity.pk,), countdown=10)


def uninstall_slack_integration(organization, user):
    slack_team_identity = organization.slack_team_identity
    if slack_team_identity is not None:
        clean_slack_integration_leftovers.apply_async((organization.pk,))
        write_chatops_insight_log(
            author=user,
            event_name=ChatOpsEvent.WORKSPACE_DISCONNECTED,
            chatops_type=ChatOpsTypePlug.SLACK.value,
        )
        unpopulate_slack_user_identities(organization.pk, True)
    else:
        raise SlackInstallationExc("Failed to uninstall Slack integration. Organization has no Slack integration.")
