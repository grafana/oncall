from unittest.mock import patch

import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.api.permissions import LegacyAccessControlRole
from apps.schedules.models import OnCallScheduleWeb
from apps.slack.tasks import clean_slack_integration_leftovers, unpopulate_slack_user_identities
from apps.user_management.models import User


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
    ],
)
def test_reset_slack_integration_permissions(
    make_organization_and_user_with_plugin_token, load_slack_urls, make_user_auth_headers, role, expected_status
):
    settings.FEATURE_SLACK_INTEGRATION_ENABLED = True

    _, user, token = make_organization_and_user_with_plugin_token(role=role)
    client = APIClient()

    url = reverse("reset-slack")
    with patch("apps.slack.views.ResetSlackView.post", return_value=Response(status=status.HTTP_200_OK)):
        response = client.post(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
def test_clean_slack_integration_leftovers(
    make_organization_with_slack_team_identity,
    make_alert_receive_channel,
    make_channel_filter,
    make_slack_user_group,
    make_schedule,
):
    organization, slack_team_identity = make_organization_with_slack_team_identity()

    # create channel filter with Slack channel
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(alert_receive_channel, slack_channel_id="test")

    # create schedule with Slack channel and user group
    user_group = make_slack_user_group(slack_team_identity)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb, channel="test", user_group=user_group)

    # clean Slack integration leftovers
    clean_slack_integration_leftovers(organization.pk)
    channel_filter.refresh_from_db()
    schedule.refresh_from_db()

    # check that references to Slack objects are removed
    assert channel_filter.slack_channel_id is None
    assert schedule.channel is None
    assert schedule.user_group is None


@pytest.mark.django_db
def test_unpopulate_slack_user_identities(
    make_organization_and_user_with_slack_identities, make_user_with_slack_user_identity
):
    # create organization and user with Slack connected
    organization, user, slack_team_identity, _ = make_organization_and_user_with_slack_identities()

    # create & delete user with Slack connected
    deleted_user, _ = make_user_with_slack_user_identity(slack_team_identity, organization)
    User.objects.filter(pk=deleted_user.pk).delete()

    # unpopulate Slack user identities
    unpopulate_slack_user_identities(organization.pk, force=True)
    user.refresh_from_db()
    deleted_user.refresh_from_db()
    organization.refresh_from_db()

    # check that references to Slack user identities are removed
    assert user.slack_user_identity is None
    assert deleted_user.slack_user_identity is None

    # check that Slack specific info is reset for organization
    assert organization.slack_team_identity is None
    assert organization.general_log_channel_id is None
