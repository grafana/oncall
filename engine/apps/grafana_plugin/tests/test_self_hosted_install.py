import json
from unittest.mock import patch

import pytest
from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

GRAFANA_TOKEN = "TEST_TOKEN"
STACK_ID = 1
ORG_ID = 5
GRAFANA_API_URL = "hello.com"
LICENSE = "OpenSource"
STACK_SLUG = "asdfasdf"
ORG_SLUG = "hellooo"
ORG_TITLE = "nmvcnmvnmvc"
REGION_SLUG = "nmcvnmcvnmcvnmcv"
CLUSTER_SLUG = "nmcvnmcvnmcvnmcvnmcv"
SELF_HOSTED_SETTINGS = {
    "GRAFANA_API_URL": GRAFANA_API_URL,
    "STACK_ID": STACK_ID,
    "ORG_ID": ORG_ID,
    "LICENSE": LICENSE,
    "STACK_SLUG": STACK_SLUG,
    "ORG_SLUG": ORG_SLUG,
    "ORG_TITLE": ORG_TITLE,
    "REGION_SLUG": REGION_SLUG,
    "CLUSTER_SLUG": CLUSTER_SLUG,
}

UNABLE_TO_FIND_GRAFANA_ERROR_MSG = f"Unable to connect to the specified Grafana API - {GRAFANA_API_URL}"
UNAUTHED_GRAFANA_API_ERROR_MSG = (
    f"You are not authorized to communicate with the specified Grafana API - {GRAFANA_API_URL}"
)


@pytest.fixture
def make_self_hosted_install_header():
    def _make_instance_context_header(token):
        return {
            "HTTP_X-Instance-Context": json.dumps({"grafana_token": token}),
        }

    return _make_instance_context_header


@override_settings(LICENSE=settings.CLOUD_LICENSE_NAME)
def test_a_cloud_license_gets_an_unauthorized_error(make_self_hosted_install_header):
    client = APIClient()
    url = reverse("grafana-plugin:self-hosted-install")
    response = client.post(url, format="json", **make_self_hosted_install_header(GRAFANA_TOKEN))

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize(
    "grafana_api_status_code,expected_error_msg",
    [
        (status.HTTP_404_NOT_FOUND, UNABLE_TO_FIND_GRAFANA_ERROR_MSG),
        (status.HTTP_401_UNAUTHORIZED, UNAUTHED_GRAFANA_API_ERROR_MSG),
        (status.HTTP_401_UNAUTHORIZED, UNAUTHED_GRAFANA_API_ERROR_MSG),
    ],
)
@override_settings(SELF_HOSTED_SETTINGS=SELF_HOSTED_SETTINGS)
@patch("apps.grafana_plugin.views.self_hosted_install.GrafanaAPIClient")
def test_it_properly_handles_errors_from_the_grafana_api(
    mocked_grafana_api_client, make_self_hosted_install_header, grafana_api_status_code, expected_error_msg
):
    mocked_grafana_api_client.return_value.check_token.return_value = (None, {"status_code": grafana_api_status_code})

    client = APIClient()
    url = reverse("grafana-plugin:self-hosted-install")
    response = client.post(url, format="json", **make_self_hosted_install_header(GRAFANA_TOKEN))

    mocked_grafana_api_client.assert_called_once_with(api_url=GRAFANA_API_URL, api_token=GRAFANA_TOKEN)
    mocked_grafana_api_client.return_value.check_token.assert_called_once_with()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["error"] == expected_error_msg


@override_settings(SELF_HOSTED_SETTINGS=SELF_HOSTED_SETTINGS)
@pytest.mark.django_db
@patch("apps.grafana_plugin.views.self_hosted_install.GrafanaAPIClient")
@patch("apps.grafana_plugin.views.self_hosted_install.sync_organization")
@patch("apps.grafana_plugin.views.self_hosted_install.Organization.provision_plugin")
@patch("apps.grafana_plugin.views.self_hosted_install.Organization.revoke_plugin")
def test_if_organization_exists_it_is_updated(
    mocked_revoke_plugin,
    mocked_provision_plugin,
    mocked_sync_organization,
    mocked_grafana_api_client,
    make_self_hosted_install_header,
    make_organization,
):
    organization = make_organization(stack_id=STACK_ID, org_id=ORG_ID)
    provision_plugin_response = {"stackId": STACK_ID, "orgId": ORG_ID, "onCallToken": "HELLOOO", "license": LICENSE}

    mocked_provision_plugin.return_value = provision_plugin_response
    mocked_grafana_api_client.return_value.check_token.return_value = (None, {"status_code": status.HTTP_200_OK})
    mocked_grafana_api_client.return_value.is_rbac_enabled_for_organization.return_value = True

    client = APIClient()
    url = reverse("grafana-plugin:self-hosted-install")
    response = client.post(url, format="json", **make_self_hosted_install_header(GRAFANA_TOKEN))

    mocked_grafana_api_client.assert_called_once_with(api_url=GRAFANA_API_URL, api_token=GRAFANA_TOKEN)
    mocked_grafana_api_client.return_value.check_token.assert_called_once_with()
    mocked_grafana_api_client.return_value.is_rbac_enabled_for_organization.assert_called_once_with()

    mocked_sync_organization.assert_called_once_with(organization)
    mocked_provision_plugin.assert_called_once_with()
    mocked_revoke_plugin.assert_called_once_with()

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data == {"error": None, **provision_plugin_response}

    organization.refresh_from_db()

    assert organization.grafana_url == GRAFANA_API_URL
    assert organization.api_token == GRAFANA_TOKEN
    assert organization.is_rbac_permissions_enabled is True


@override_settings(SELF_HOSTED_SETTINGS=SELF_HOSTED_SETTINGS)
@pytest.mark.django_db
@patch("apps.grafana_plugin.views.self_hosted_install.GrafanaAPIClient")
@patch("apps.grafana_plugin.views.self_hosted_install.sync_organization")
@patch("apps.grafana_plugin.views.self_hosted_install.Organization.provision_plugin")
@patch("apps.grafana_plugin.views.self_hosted_install.Organization.revoke_plugin")
def test_if_organization_does_not_exist_it_is_created(
    mocked_revoke_plugin,
    mocked_provision_plugin,
    mocked_sync_organization,
    mocked_grafana_api_client,
    make_self_hosted_install_header,
):
    provision_plugin_response = {"stackId": STACK_ID, "orgId": ORG_ID, "onCallToken": "HELLOOO", "license": LICENSE}

    mocked_provision_plugin.return_value = provision_plugin_response
    mocked_grafana_api_client.return_value.check_token.return_value = (None, {"status_code": status.HTTP_200_OK})
    mocked_grafana_api_client.return_value.is_rbac_enabled_for_organization.return_value = True

    client = APIClient()
    url = reverse("grafana-plugin:self-hosted-install")
    response = client.post(url, format="json", **make_self_hosted_install_header(GRAFANA_TOKEN))

    from apps.user_management.models import Organization

    organization = Organization.objects.filter(stack_id=STACK_ID, org_id=ORG_ID).first()

    mocked_grafana_api_client.assert_called_once_with(api_url=GRAFANA_API_URL, api_token=GRAFANA_TOKEN)
    mocked_grafana_api_client.return_value.check_token.assert_called_once_with()
    mocked_grafana_api_client.return_value.is_rbac_enabled_for_organization.assert_called_once_with()

    mocked_sync_organization.assert_called_once_with(organization)
    mocked_provision_plugin.assert_called_once_with()
    assert not mocked_revoke_plugin.called

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data == {"error": None, **provision_plugin_response}

    assert organization.stack_id == STACK_ID
    assert organization.stack_slug == STACK_SLUG
    assert organization.org_slug == ORG_SLUG
    assert organization.org_title == ORG_TITLE
    assert organization.region_slug == REGION_SLUG
    assert organization.grafana_url == GRAFANA_API_URL
    assert organization.api_token == GRAFANA_TOKEN
    assert organization.is_rbac_permissions_enabled is True
