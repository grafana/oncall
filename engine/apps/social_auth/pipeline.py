import logging
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponse
from rest_framework import status
from social_core.exceptions import AuthForbidden

from apps.slack.tasks import populate_slack_channels_for_team, populate_slack_usergroups_for_team
from apps.social_auth.exceptions import InstallMultiRegionSlackException
from common.constants.slack_auth import SLACK_AUTH_SLACK_USER_ALREADY_CONNECTED_ERROR, SLACK_AUTH_WRONG_WORKSPACE_ERROR
from common.insight_log import ChatOpsEvent, ChatOpsTypePlug, write_chatops_insight_log
from common.oncall_gateway import check_slack_installation_possible, create_slack_connector

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
    from apps.slack.models import SlackTeamIdentity

    # Continue pipeline step only if it was installation
    if backend.name != "slack-install-free":
        return

    if organization.slack_team_identity is not None:
        # means that organization already has Slack integration
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    slack_team_id = response["team"]["id"]
    if settings.FEATURE_MULTIREGION_ENABLED and not check_slack_installation_possible(
        str(organization.uuid), slack_team_id, settings.ONCALL_BACKEND_REGION
    ):
        raise InstallMultiRegionSlackException

    slack_team_identity, is_slack_team_identity_created = SlackTeamIdentity.objects.get_or_create(
        slack_id=slack_team_id,
    )
    # update slack oauth fields by data from response
    slack_team_identity.update_oauth_fields(user, organization, response)
    if settings.FEATURE_MULTIREGION_ENABLED:
        create_slack_connector(str(organization.uuid), slack_team_id, settings.ONCALL_BACKEND_REGION)
    populate_slack_channels_for_team.apply_async((slack_team_identity.pk,))
    user.slack_user_identity.update_profile_info()
    # todo slack: do we need update info for all existing slack users in slack team?
    # populate_slack_user_identities.apply_async((organization.pk,))
    populate_slack_usergroups_for_team.apply_async((slack_team_identity.pk,), countdown=10)


def delete_slack_auth_token(strategy, *args, **kwargs):
    strategy.request.auth.delete()
