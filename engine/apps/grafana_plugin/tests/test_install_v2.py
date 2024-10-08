from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.grafana_plugin.views.sync_v2 import SyncException
from common.api_helpers.errors import INVALID_SELF_HOSTED_ID


@pytest.mark.django_db
def test_install_v2_error_encoding(make_organization_and_user_with_plugin_token, make_user_auth_headers):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    auth_headers = make_user_auth_headers(user, token)

    exc = SyncException(INVALID_SELF_HOSTED_ID)

    with patch("apps.grafana_plugin.views.InstallV2View.do_sync", side_effect=exc):
        response = client.post(reverse("grafana-plugin:install-v2"), format="json", **auth_headers)
        assert response.data["code"] == INVALID_SELF_HOSTED_ID.code
        assert response.data["message"] == INVALID_SELF_HOSTED_ID.message
        assert response.status_code == status.HTTP_400_BAD_REQUEST
