# Response example from Slack docs https://api.slack.com/methods/oauth.v2.access#examples
from unittest.mock import patch

import pytest

from apps.slack.client import SlackClient
from apps.slack.installation import SlackInstallationExc, install_slack_integration, uninstall_slack_integration
from common.constants.slack_auth import SLACK_OAUTH_ACCESS_RESPONSE

users_profile_get_response = {
    "ok": True,
    "user": {
        "id": "W012A3CDE",
        "team_id": "T012AB3C4",
        "name": "spengler",
        "deleted": False,
        "color": "9f69e7",
        "real_name": "Egon Spengler",
        "tz": "America/Los_Angeles",
        "tz_label": "Pacific Daylight Time",
        "tz_offset": -25200,
        "profile": {
            "avatar_hash": "ge3b51ca72de",
            "status_text": "Print is dead",
            "status_emoji": ":books:",
            "real_name": "Egon Spengler",
            "display_name": "spengler",
            "real_name_normalized": "Egon Spengler",
            "display_name_normalized": "spengler",
            "email": "spengler@ghostbusters.example.com",
            "image_original": "https://.../avatar/e3b51ca72dee4ef87916ae2b9240df50.jpg",
            "image_24": "https://.../avatar/e3b51ca72dee4ef87916ae2b9240df50.jpg",
            "image_32": "https://.../avatar/e3b51ca72dee4ef87916ae2b9240df50.jpg",
            "image_48": "https://.../avatar/e3b51ca72dee4ef87916ae2b9240df50.jpg",
            "image_72": "https://.../avatar/e3b51ca72dee4ef87916ae2b9240df50.jpg",
            "image_192": "https://.../avatar/e3b51ca72dee4ef87916ae2b9240df50.jpg",
            "image_512": "https://.../avatar/e3b51ca72dee4ef87916ae2b9240df50.jpg",
            "team": "T012AB3C4",
        },
        "is_admin": True,
        "is_owner": False,
        "is_primary_owner": False,
        "is_restricted": False,
        "is_ultra_restricted": False,
        "is_bot": False,
        "updated": 1502138686,
        "is_app_user": False,
        "has_2fa": False,
    },
}


@patch("apps.slack.tasks.populate_slack_channels_for_team.apply_async", return_value=None)
@patch("apps.slack.tasks.populate_slack_usergroups_for_team.apply_async", return_value=None)
@patch.object(SlackClient, "users_info", return_value=users_profile_get_response)
@pytest.mark.django_db
def test_install_slack_integration(
    mock_populate_slack_channels_for_team,
    mock_populate_slack_usergroups_for_team,
    mock_users_info,
    make_organization_and_user,
):
    organization, user = make_organization_and_user()
    install_slack_integration(organization, user, SLACK_OAUTH_ACCESS_RESPONSE)

    assert organization.slack_team_identity is not None
    # test that two most important fields are set: id of slack workspace and api acess token
    assert organization.slack_team_identity.slack_id == SLACK_OAUTH_ACCESS_RESPONSE["team"]["id"]
    assert organization.slack_team_identity.bot_access_token == SLACK_OAUTH_ACCESS_RESPONSE["access_token"]

    # install_slack_integration links instgallers's slack profile to OnCall
    assert user.slack_user_identity is not None

    # assert that installer slack profile is linked to OnCall user
    assert user.slack_user_identity.slack_id == SLACK_OAUTH_ACCESS_RESPONSE["authed_user"]["id"]

    # assert that we populated user's profile info
    assert user.slack_user_identity.cached_slack_login == users_profile_get_response["user"]["name"]

    # assert that we ran task for fetching data from slack
    assert mock_populate_slack_channels_for_team.called
    assert mock_populate_slack_usergroups_for_team.called


@pytest.mark.django_db
def test_install_slack_integration_raises_exception_for_existing_integration(
    make_organization_and_user, make_slack_team_identity
):
    slack_team_identity = make_slack_team_identity()
    organization, user = make_organization_and_user()
    organization.slack_team_identity = slack_team_identity
    organization.save()

    with pytest.raises(SlackInstallationExc):
        install_slack_integration(organization, user, SLACK_OAUTH_ACCESS_RESPONSE)


@patch("apps.slack.tasks.clean_slack_integration_leftovers.apply_async", return_value=None)
@pytest.mark.django_db
def test_uninstall_slack_integration(
    mock_clean_slack_integration_leftovers,
    make_organization_and_user,
    make_slack_team_identity,
    make_slack_user_identity,
):
    slack_team_identity = make_slack_team_identity()
    organization, user = make_organization_and_user()
    organization.slack_team_identity = slack_team_identity
    organization.save()
    organization.refresh_from_db()

    slack_user_identity = make_slack_user_identity(slack_team_identity=slack_team_identity)
    user.slack_user_identity = slack_user_identity
    user.save()
    user.refresh_from_db()

    uninstall_slack_integration(organization, user)

    organization.refresh_from_db()
    user.refresh_from_db()
    assert organization.slack_team_identity is None
    assert user.slack_user_identity is None

    # assert that we ran task for fetching data from slack
    assert mock_clean_slack_integration_leftovers.called


@pytest.mark.django_db
def test_uninstall_slack_integration_raises_exception_for_non_existing_integration(
    make_organization_and_user,
):
    organization, user = make_organization_and_user()

    with pytest.raises(SlackInstallationExc):
        uninstall_slack_integration(organization, user)
