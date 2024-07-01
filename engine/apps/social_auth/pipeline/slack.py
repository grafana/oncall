import logging
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponse
from rest_framework import status

from apps.chatops_proxy.utils import can_link_slack_team, link_slack_team
from apps.slack.installation import SlackInstallationExc, install_slack_integration
from apps.social_auth.backends import SLACK_INSTALLATION_BACKEND
from apps.social_auth.exceptions import InstallMultiRegionSlackException
from common.constants.slack_auth import SLACK_AUTH_SLACK_USER_ALREADY_CONNECTED_ERROR, SLACK_AUTH_WRONG_WORKSPACE_ERROR
from common.insight_log import ChatOpsEvent, ChatOpsTypePlug, write_chatops_insight_log

logger = logging.getLogger(__name__)


def connect_user_to_slack(response, backend, strategy, user, organization, *args, **kwargs):
    from apps.slack.models import SlackUserIdentity

    # Continue pipeline step only if it was installation
    if backend.name != "slack-login":
        return

    slack_team_identity = organization.slack_team_identity
    slack_user_id = response["authed_user"]["id"]

    redirect_to = "/a/grafana-oncall-app/users/me/"
    base_url_to_redirect = urljoin(organization.grafana_url, redirect_to)

    if slack_team_identity is None:
        # means that organization doesn't have slack integration, so user cannot connect their account to slack
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    if slack_team_identity.slack_id != response["team"]["id"]:
        # means that user authed in another slack workspace that is not connected to their organization
        # change redirect url to show user error message and save it in session param
        url = base_url_to_redirect + f"?slack_error={SLACK_AUTH_WRONG_WORKSPACE_ERROR}"
        strategy.session[REDIRECT_FIELD_NAME] = url
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    if organization.users.filter(slack_user_identity__slack_id=slack_user_id).exists():
        # means that slack user has already been connected to another user in current organization
        url = base_url_to_redirect + f"?slack_error={SLACK_AUTH_SLACK_USER_ALREADY_CONNECTED_ERROR}"
        strategy.session[REDIRECT_FIELD_NAME] = url
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    # at this point everything is correct and we can create the SlackUserIdentity
    # be sure to clear any pre-existing sessions, in case the user previously enecountered errors we want
    # to be sure to clear these so they do not see them again
    strategy.session.flush()

    slack_user_identity, _ = SlackUserIdentity.objects.get_or_create(
        slack_id=slack_user_id,
        slack_team_identity=slack_team_identity,
        defaults={
            "cached_slack_email": response["user"]["email"],
        },
    )

    write_chatops_insight_log(
        author=user,
        event_name=ChatOpsEvent.USER_LINKED,
        chatops_type=ChatOpsTypePlug.SLACK.value,
        linked_user=user.username,
        linked_user_id=user.public_primary_key,
    )
    user.slack_user_identity = slack_user_identity
    user.save(update_fields=["slack_user_identity"])

    slack_user_identity.update_profile_info()


def populate_slack_identities(response, backend, user, organization, **kwargs):
    # Continue pipeline step only if it was installation
    if backend.name != SLACK_INSTALLATION_BACKEND:
        return

    slack_team_id = response["team"]["id"]
    if settings.FEATURE_MULTIREGION_ENABLED and not settings.UNIFIED_SLACK_APP_ENABLED:
        can_link = can_link_slack_team(str(organization.uuid), slack_team_id, settings.ONCALL_BACKEND_REGION)
        if not can_link:
            raise InstallMultiRegionSlackException
    try:
        install_slack_integration(organization, user, response)
    except SlackInstallationExc:
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)
    if settings.FEATURE_MULTIREGION_ENABLED and not settings.UNIFIED_SLACK_APP_ENABLED:
        link_slack_team(str(organization.uuid), slack_team_id)


def delete_slack_auth_token(strategy, *args, **kwargs):
    strategy.request.auth.delete()
