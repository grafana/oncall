from unittest.mock import patch

import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from common.constants.role import Role


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_403_FORBIDDEN),
        (Role.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_reset_slack_integration_permissions(
    make_organization_and_user_with_plugin_token, role, expected_status, load_slack_urls, make_user_auth_headers
):
    settings.FEATURE_SLACK_INTEGRATION_ENABLED = True

    _, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()

    url = reverse("reset-slack")
    with patch("apps.slack.views.ResetSlackView.post", return_value=Response(status=status.HTTP_200_OK)):
        response = client.post(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status
