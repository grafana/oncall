from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

GRAFANA_TOKEN = "TESTTOKEN"


@patch("apps.grafana_plugin.views.install.sync_organization", return_value=None)
@pytest.mark.django_db
def test_it_triggers_an_organization_sync_and_saves_the_grafana_token(
    mocked_sync_organization, make_organization_and_user_with_plugin_token, make_user_auth_headers
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    auth_headers = make_user_auth_headers(user, token, grafana_token=GRAFANA_TOKEN)
    response = client.post(reverse("grafana-plugin:install"), format="json", **auth_headers)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    mocked_sync_organization.assert_called_once_with(organization)

    # make sure api token is saved on the org
    organization.refresh_from_db()
    assert organization.api_token == GRAFANA_TOKEN
