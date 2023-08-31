import pytest
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.user_management.models import Organization

GRAFANA_TOKEN = "TESTTOKEN"
GRAFANA_URL = "hello.com"
LICENSE = "asdfasdf"
VERSION = "asdfasdfasdf"
BASE_URL = "http://asdasdqweqweqw.com/oncall"
GRAFANA_CONTEXT_DATA = {"IsAnonymous": False}
SETTINGS = {"LICENSE": LICENSE, "VERSION": VERSION, "BASE_URL": BASE_URL}


def _check_status_response(auth_headers, client):
    response = client.post(reverse("grafana-plugin:status"), format="json", **auth_headers)
    response_data = response.data
    assert response.status_code == status.HTTP_200_OK
    assert response_data["token_ok"] is True
    assert response_data["is_installed"] is True
    assert response_data["allow_signup"] is True
    assert response_data["is_user_anonymous"] is False
    assert response_data["license"] == LICENSE
    assert response_data["version"] == VERSION
    assert response_data["api_url"] == BASE_URL


@pytest.mark.django_db
@override_settings(**SETTINGS)
def test_token_ok_is_based_on_grafana_api_check_token_response(
    make_organization_and_user_with_plugin_token, make_user_auth_headers
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    organization.grafana_url = GRAFANA_URL
    organization.api_token_status = Organization.API_TOKEN_STATUS_OK
    organization.save(update_fields=["grafana_url", "api_token_status"])

    client = APIClient()
    url = reverse("grafana-plugin:status")
    response = client.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    auth_headers = make_user_auth_headers(
        user, token, grafana_token=GRAFANA_TOKEN, grafana_context_data=GRAFANA_CONTEXT_DATA
    )
    _check_status_response(auth_headers, client)


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

    # should consider removing the DynamicSetting logic because technically this
    # condition will never be reached in the code...
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
@override_settings(**SETTINGS)
def test_status_mobile_app_auth_token(
    make_organization_and_user_with_mobile_app_auth_token,
    make_user_auth_headers,
):
    organization, user, auth_token = make_organization_and_user_with_mobile_app_auth_token()
    organization.grafana_url = GRAFANA_URL
    organization.api_token_status = Organization.API_TOKEN_STATUS_OK
    organization.save(update_fields=["grafana_url", "api_token_status"])

    client = APIClient()
    url = reverse("grafana-plugin:status")
    response = client.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    auth_headers = {"HTTP_AUTHORIZATION": f"{auth_token}"}
    _check_status_response(auth_headers, client)
