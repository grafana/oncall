from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.api.permissions import LegacyAccessControlRole


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
    ],
)
def test_slack_channels_list_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()

    url = reverse("api-internal:slack_channel-list")

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    with patch(
        "apps.api.views.slack_channel.SlackChannelView.list",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
    ],
)
def test_slack_channels_detail_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_slack_channel,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    slack_channel = make_slack_channel(organization.slack_team_identity)
    client = APIClient()

    url = reverse("api-internal:slack_channel-detail", kwargs={"pk": slack_channel.public_primary_key})

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    with patch(
        "apps.api.views.slack_channel.SlackChannelView.retrieve",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        assert response.status_code == expected_status
