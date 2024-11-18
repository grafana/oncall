from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.api.permissions import LegacyAccessControlRole


# Testing permissions, not view itself. So mock is ok here
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
def test_set_org_default_slack_channel_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()

    url = reverse("api-internal:set-default-slack-channel")
    with patch(
        "apps.api.views.organization.SetDefaultSlackChannel.post", return_value=Response(status=status.HTTP_200_OK)
    ):
        response = client.post(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
def test_set_organization_slack_default_channel(
    make_organization_and_user_with_plugin_token,
    make_slack_team_identity,
    make_slack_channel,
    make_user_auth_headers,
):
    slack_team_identity = make_slack_team_identity()
    slack_channel = make_slack_channel(slack_team_identity)

    organization, user, token = make_organization_and_user_with_plugin_token()
    organization.slack_team_identity = slack_team_identity
    organization.save()

    auth_headers = make_user_auth_headers(user, token)

    assert organization.default_slack_channel is None

    client = APIClient()

    def _update_default_slack_channel(slack_channel_id):
        # this endpoint doesn't return any data..
        response = client.post(
            reverse("api-internal:set-default-slack-channel"),
            data={
                "id": slack_channel_id,
            },
            format="json",
            **auth_headers,
        )
        assert response.status_code == status.HTTP_200_OK

    def _assert_default_slack_channel_is_updated(slack_channel_id):
        response = client.get(reverse("api-internal:api-organization"), format="json", **auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["slack_channel"] == slack_channel_id

    _update_default_slack_channel(slack_channel.public_primary_key)
    _assert_default_slack_channel_is_updated(
        {
            "id": slack_channel.public_primary_key,
            "display_name": slack_channel.name,
            "slack_id": slack_channel.slack_id,
        }
    )

    # NOTE: currently the endpoint doesn't allow to remove default slack channel, if and when it does, uncomment this
    # _update_default_slack_channel(None)
    # _assert_default_slack_channel_is_updated(None)
