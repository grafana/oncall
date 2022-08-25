import logging
from urllib.parse import urljoin

from django.apps import apps
from django.http import HttpResponse
from rest_framework import status
from social_core.exceptions import AuthForbidden

from apps.slack.tasks import populate_slack_channels_for_team, populate_slack_usergroups_for_team
from common.constants.slack_auth import (
    REDIRECT_AFTER_SLACK_INSTALL,
    SLACK_AUTH_SLACK_USER_ALREADY_CONNECTED_ERROR,
    SLACK_AUTH_WRONG_WORKSPACE_ERROR,
)
from common.insight_log import ChatOpsEvent, ChatOpsType, write_chatops_insight_log

logger = logging.getLogger(__name__)


def set_user_and_organization_from_request(backend, strategy, *args, **kwargs):
    user = strategy.request.user
    organization = strategy.request.auth.organization
    if user is None or organization is None:
        return HttpResponse(str(AuthForbidden(backend)), status=status.HTTP_401_UNAUTHORIZED)
    return {
        "user": user,
        "organization": organization,
    }


def connect_user_to_slack(response, backend, strategy, user, organization, *args, **kwargs):
    SlackUserIdentity = apps.get_model("slack", "SlackUserIdentity")

    # Continue pipeline step only if it was installation
    if backend.name != "slack-login":
        return

    slack_team_identity = organization.slack_team_identity
    slack_user_id = response["authed_user"]["id"]

    if slack_team_identity is None:
        # means that organization doesn't have slack integration, so user cannot connect their account to slack
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)
    if slack_team_identity.slack_id != response["team"]["id"]:
        # means that user authed in another slack workspace that is not connected to their organization
        # change redirect url to show user error message and save it in session param
        url = urljoin(
            strategy.session[REDIRECT_AFTER_SLACK_INSTALL],
            f"?page=users&slack_error={SLACK_AUTH_WRONG_WORKSPACE_ERROR}",
        )
        strategy.session[REDIRECT_AFTER_SLACK_INSTALL] = url
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    if organization.users.filter(slack_user_identity__slack_id=slack_user_id).exists():
        # means that slack user has already been connected to another user in current organization
        url = urljoin(
            strategy.session[REDIRECT_AFTER_SLACK_INSTALL],
            f"?page=users&slack_error={SLACK_AUTH_SLACK_USER_ALREADY_CONNECTED_ERROR}",
        )
        strategy.session[REDIRECT_AFTER_SLACK_INSTALL] = url
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

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
        chatops_type=ChatOpsType.SLACK,
        linked_user=user.username,
        linked_user_id=user.public_primary_key,
    )
    user.slack_user_identity = slack_user_identity
    user.save(update_fields=["slack_user_identity"])

    slack_user_identity.update_profile_info()


def populate_slack_identities(response, backend, user, organization, **kwargs):
    SlackTeamIdentity = apps.get_model("slack", "SlackTeamIdentity")

    # Continue pipeline step only if it was installation
    if backend.name != "slack-install-free":
        return

    if organization.slack_team_identity is not None:
        # means that organization already has slack integration
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    slack_team_id = response["team"]["id"]
    slack_team_identity, is_slack_team_identity_created = SlackTeamIdentity.objects.get_or_create(
        slack_id=slack_team_id,
    )

    # update slack oauth fields by data from response
    slack_team_identity.update_oauth_fields(user, organization, response)

    populate_slack_channels_for_team.apply_async((slack_team_identity.pk,))
    user.slack_user_identity.update_profile_info()
    # todo slack: do we need update info for all existing slack users in slack team?
    # populate_slack_user_identities.apply_async((organization.pk,))
    populate_slack_usergroups_for_team.apply_async((slack_team_identity.pk,), countdown=10)


def delete_slack_auth_token(strategy, *args, **kwargs):
    strategy.request.auth.delete()
