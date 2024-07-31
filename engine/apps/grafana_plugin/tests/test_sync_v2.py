from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.api.permissions import LegacyAccessControlRole


@pytest.mark.django_db
def test_auth_success(make_organization_and_user_with_plugin_token, make_user_auth_headers):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    auth_headers = make_user_auth_headers(user, token)

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

    auth_headers = make_user_auth_headers(user, token)
    with patch("apps.grafana_plugin.views.sync_v2.SyncV2View.do_sync", return_value=organization) as mock_sync:
        response = client.post(reverse("grafana-plugin:sync-v2"), format="json", **auth_headers)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert not mock_sync.called
