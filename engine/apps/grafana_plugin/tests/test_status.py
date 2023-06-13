from unittest.mock import patch

import pytest
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

GRAFANA_TOKEN = "TESTTOKEN"
GRAFANA_URL = "hello.com"
LICENSE = "asdfasdf"
VERSION = "asdfasdfasdf"
GRAFANA_CONTEXT_DATA = {"IsAnonymous": False}
SETTINGS = {"LICENSE": LICENSE, "VERSION": VERSION}


@pytest.mark.django_db
@override_settings(**SETTINGS)
@patch("apps.grafana_plugin.views.status.GrafanaAPIClient")
def test_token_ok_is_based_on_grafana_api_check_token_response(
    mocked_grafana_api_client, make_organization_and_user_with_plugin_token, make_user_auth_headers
):
    mocked_grafana_api_client.return_value.check_token.return_value = (None, {"connected": True})

    organization, user, token = make_organization_and_user_with_plugin_token()
    organization.grafana_url = GRAFANA_URL
    organization.save(update_fields=["grafana_url"])

    client = APIClient()
    auth_headers = make_user_auth_headers(
        user, token, grafana_token=GRAFANA_TOKEN, grafana_context_data=GRAFANA_CONTEXT_DATA
    )
    response = client.get(reverse("grafana-plugin:status"), format="json", **auth_headers)
    response_data = response.data

    assert response.status_code == status.HTTP_200_OK
    assert response_data["token_ok"] is True
    assert response_data["is_installed"] is True
    assert response_data["allow_signup"] is True
    assert response_data["is_user_anonymous"] is False
    assert response_data["license"] == LICENSE
    assert response_data["version"] == VERSION

    assert mocked_grafana_api_client.called_once_with(api_url=GRAFANA_URL, api_token=GRAFANA_TOKEN)
    assert mocked_grafana_api_client.return_value.check_token.called_once_with()


@pytest.mark.django_db
@override_settings(**SETTINGS)
def test_allow_signup(make_organization_and_user_with_plugin_token, make_user_auth_headers):
    organization, user, token = make_organization_and_user_with_plugin_token()
    # change the stack id so that this org isn't found
    organization.stack_id = 494509
    organization.save(update_fields=["stack_id"])

    client = APIClient()
    auth_headers = make_user_auth_headers(
        user, token, grafana_token=GRAFANA_TOKEN, grafana_context_data=GRAFANA_CONTEXT_DATA
    )
    response = client.get(reverse("grafana-plugin:status"), format="json", **auth_headers)

    # if the org doesn't exist this will never return 200 due to
    # the PluginTokenVerified permission class..
    # should consider removing the DynamicSetting logic because technically this
    # condition will never be reached in the code...
    assert response.status_code == status.HTTP_403_FORBIDDEN
