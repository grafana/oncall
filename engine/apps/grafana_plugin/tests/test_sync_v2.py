from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.api.permissions import LegacyAccessControlRole
from apps.grafana_plugin.tasks.sync_v2 import start_sync_organizations_v2


@pytest.mark.django_db
def test_auth_success(make_organization_and_user_with_plugin_token, make_user_auth_headers):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    auth_headers = make_user_auth_headers(user, token)
    del auth_headers["HTTP_X-Grafana-Context"]

    with patch("apps.grafana_plugin.views.sync_v2.SyncV2View.do_sync", return_value=organization) as mock_sync:
        response = client.post(reverse("grafana-plugin:sync-v2"), format="json", **auth_headers)

    assert response.status_code == status.HTTP_200_OK
    assert mock_sync.called


@pytest.mark.django_db
def test_invalid_auth(make_organization_and_user_with_plugin_token, make_user_auth_headers):
    organization, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)
    client = APIClient()

    auth_headers = make_user_auth_headers(user, "invalid-token")

    with patch("apps.grafana_plugin.views.sync_v2.SyncV2View.do_sync", return_value=organization) as mock_sync:
        response = client.post(reverse("grafana-plugin:sync-v2"), format="json", **auth_headers)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert not mock_sync.called

    auth_headers = make_user_auth_headers(None, token, organization=organization)
    del auth_headers["HTTP_X-Instance-Context"]

    with patch("apps.grafana_plugin.views.sync_v2.SyncV2View.do_sync", return_value=organization) as mock_sync:
        response = client.post(reverse("grafana-plugin:sync-v2"), format="json", **auth_headers)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert not mock_sync.called


@pytest.mark.parametrize(
    "api_token, sync_called",
    [
        ("", False),
        ("abc", False),
        ("glsa_abcdefghijklmnopqrstuvwxyz", True),
    ],
)
@pytest.mark.django_db
def test_skip_org_without_api_token(make_organization, api_token, sync_called):
    make_organization(api_token=api_token)

    with patch(
        "apps.grafana_plugin.helpers.GrafanaAPIClient.sync",
        return_value=(
            None,
            {
                "url": "",
                "connected": True,
                "status_code": status.HTTP_200_OK,
                "message": "",
            },
        ),
    ):
        with patch(
            "apps.grafana_plugin.tasks.sync_v2.sync_organizations_v2.apply_async", return_value=None
        ) as mock_sync:
            start_sync_organizations_v2()
            assert mock_sync.called == sync_called
