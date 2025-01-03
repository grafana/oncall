import typing
from unittest.mock import patch

import httpretty
import pytest
from rest_framework import exceptions
from rest_framework.test import APIRequestFactory

from apps.api.permissions import LegacyAccessControlRole
from apps.auth_token.auth import X_GRAFANA_INSTANCE_ID, GrafanaServiceAccountAuthentication
from apps.auth_token.models import ServiceAccountToken
from apps.auth_token.tests.helpers import setup_service_account_api_mocks
from apps.user_management.models import Organization
from common.constants.plugin_ids import PluginID
from settings.base import CLOUD_LICENSE_NAME, OPEN_SOURCE_LICENSE_NAME, SELF_HOSTED_SETTINGS


def fake_authenticate_credentials(organization, token):
    pass


@pytest.mark.django_db
def test_grafana_authentication_oss_inputs(make_organization, settings):
    settings.LICENSE = OPEN_SOURCE_LICENSE_NAME

    headers, token = check_common_inputs()
    organization = make_organization(
        stack_id=SELF_HOSTED_SETTINGS["STACK_ID"],
        org_id=SELF_HOSTED_SETTINGS["ORG_ID"],
        stack_slug=SELF_HOSTED_SETTINGS["STACK_SLUG"],
        org_slug=SELF_HOSTED_SETTINGS["ORG_SLUG"],
    )
    request = APIRequestFactory().get("/", **headers)
    with patch(
        "apps.auth_token.auth.GrafanaServiceAccountAuthentication.authenticate_credentials",
        wraps=fake_authenticate_credentials,
    ) as mock:
        GrafanaServiceAccountAuthentication().authenticate(request)
        mock.assert_called_once_with(organization, token)


@pytest.mark.django_db
def test_grafana_authentication_cloud_inputs(make_organization, settings):
    settings.LICENSE = CLOUD_LICENSE_NAME
    headers, token = check_common_inputs()

    test_instance_id = "123"
    headers[f"HTTP_{X_GRAFANA_INSTANCE_ID}"] = test_instance_id
    request = APIRequestFactory().get("/", **headers)
    with pytest.raises(exceptions.AuthenticationFailed):
        GrafanaServiceAccountAuthentication().authenticate(request)

    organization = make_organization(stack_id=test_instance_id)
    with patch(
        "apps.auth_token.auth.GrafanaServiceAccountAuthentication.authenticate_credentials",
        wraps=fake_authenticate_credentials,
    ) as mock:
        GrafanaServiceAccountAuthentication().authenticate(request)
        mock.assert_called_once_with(organization, token)


def check_common_inputs() -> tuple[dict[str, typing.Any], str]:
    request = APIRequestFactory().get("/")
    with pytest.raises(exceptions.AuthenticationFailed):
        GrafanaServiceAccountAuthentication().authenticate(request)

    headers = {
        "HTTP_AUTHORIZATION": "xyz",
    }
    request = APIRequestFactory().get("/", **headers)
    result = GrafanaServiceAccountAuthentication().authenticate(request)
    assert result is None

    token = f"{ServiceAccountToken.GRAFANA_SA_PREFIX}xyz"
    headers = {
        "HTTP_AUTHORIZATION": token,
    }
    request = APIRequestFactory().get("/", **headers)
    with pytest.raises(exceptions.AuthenticationFailed):
        GrafanaServiceAccountAuthentication().authenticate(request)

    return headers, token


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_grafana_authentication_missing_org():
    token = f"{ServiceAccountToken.GRAFANA_SA_PREFIX}xyz"
    headers = {
        "HTTP_AUTHORIZATION": token,
    }
    request = APIRequestFactory().get("/", **headers)

    with pytest.raises(exceptions.AuthenticationFailed) as exc:
        GrafanaServiceAccountAuthentication().authenticate(request)
    assert exc.value.detail == "Organization not found."


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_grafana_authentication_no_org_grafana_url():
    grafana_url = "http://grafana.test"
    token = f"{ServiceAccountToken.GRAFANA_SA_PREFIX}xyz"
    headers = {
        "HTTP_AUTHORIZATION": token,
        "HTTP_X_GRAFANA_URL": grafana_url,  # no org for this URL
    }
    request = APIRequestFactory().get("/", **headers)

    request_sync_url = f"{grafana_url}/api/plugins/{PluginID.ONCALL}/resources/plugin/sync?wait=true&force=true"
    httpretty.register_uri(httpretty.POST, request_sync_url, status=404)

    with pytest.raises(exceptions.Throttled) as exc:
        GrafanaServiceAccountAuthentication().authenticate(request)
    assert exc.value.detail == "Organization being synced, please retry."


@pytest.mark.parametrize("grafana_url", ["null;", "foo", ""])
@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_grafana_authentication_invalid_grafana_url(grafana_url):
    token = f"{ServiceAccountToken.GRAFANA_SA_PREFIX}xyz"
    headers = {
        "HTTP_AUTHORIZATION": token,
        "HTTP_X_GRAFANA_URL": grafana_url,  # no org for this URL
    }
    request = APIRequestFactory().get("/", **headers)

    # NOTE: no sync requests are made in this case
    with pytest.raises(exceptions.AuthenticationFailed) as exc:
        GrafanaServiceAccountAuthentication().authenticate(request)
    assert exc.value.detail == "Organization not found."


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_grafana_authentication_permissions_call_fails(make_organization):
    organization = make_organization(grafana_url="http://grafana.test")

    token = f"{ServiceAccountToken.GRAFANA_SA_PREFIX}xyz"
    headers = {
        "HTTP_AUTHORIZATION": token,
        "HTTP_X_GRAFANA_URL": organization.grafana_url,
    }
    request = APIRequestFactory().get("/", **headers)

    # setup Grafana API responses
    # permissions endpoint returns a 401
    setup_service_account_api_mocks(organization.grafana_url, perms_status=401)

    with pytest.raises(exceptions.AuthenticationFailed) as exc:
        GrafanaServiceAccountAuthentication().authenticate(request)
    assert exc.value.detail == "Invalid token."

    last_request = httpretty.last_request()
    assert last_request.method == "GET"
    expected_url = f"{organization.grafana_url}/api/access-control/user/permissions"
    assert last_request.url == expected_url
    # the request uses the given token
    assert last_request.headers["Authorization"] == f"Bearer {token}"


@pytest.mark.django_db
@pytest.mark.parametrize("grafana_url", ["http://grafana.test", "http://grafana.test/"])
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_grafana_authentication_existing_token(
    make_organization, make_service_account_for_organization, make_token_for_service_account, grafana_url
):
    # org grafana_url is consistently stored without trailing slash
    organization = make_organization(grafana_url="http://grafana.test")
    service_account = make_service_account_for_organization(organization)
    token_string = "glsa_the-token"
    token = make_token_for_service_account(service_account, token_string)

    headers = {
        "HTTP_AUTHORIZATION": token_string,
        "HTTP_X_GRAFANA_URL": grafana_url,  # trailing slash is ignored
    }
    request = APIRequestFactory().get("/", **headers)

    # setup Grafana API responses (use URL without trailing slash)
    setup_service_account_api_mocks(organization.grafana_url, {"some-perm": "value"})

    user, auth_token = GrafanaServiceAccountAuthentication().authenticate(request)

    assert user.is_service_account
    assert user.service_account == service_account
    assert user.public_primary_key == service_account.public_primary_key
    assert user.username == service_account.username
    assert user.role == LegacyAccessControlRole.NONE
    assert auth_token == token

    last_request = httpretty.last_request()
    assert last_request.method == "GET"
    expected_url = f"{organization.grafana_url}/api/access-control/user/permissions"
    assert last_request.url == expected_url
    # the request uses the given token
    assert last_request.headers["Authorization"] == f"Bearer {token_string}"


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_grafana_authentication_token_created(make_organization):
    organization = make_organization(grafana_url="http://grafana.test")
    token_string = "glsa_the-token"

    headers = {
        "HTTP_AUTHORIZATION": token_string,
        "HTTP_X_GRAFANA_URL": organization.grafana_url,
    }
    request = APIRequestFactory().get("/", **headers)

    # setup Grafana API responses
    permissions = {"some-perm": "value"}
    user_data = {"login": "some-login", "uid": "service-account:42"}
    setup_service_account_api_mocks(organization.grafana_url, permissions, user_data)

    user, auth_token = GrafanaServiceAccountAuthentication().authenticate(request)

    assert user.is_service_account
    service_account = user.service_account
    assert service_account.organization == organization
    assert user.public_primary_key == service_account.public_primary_key
    assert user.username == service_account.username
    assert service_account.grafana_id == 42
    assert service_account.login == "some-login"
    assert user.role == LegacyAccessControlRole.NONE
    assert user.permissions == [{"action": p} for p in permissions]
    assert auth_token.service_account == user.service_account

    perms_request, user_request = httpretty.latest_requests()
    for req in (perms_request, user_request):
        assert req.method == "GET"
        assert req.headers["Authorization"] == f"Bearer {token_string}"
    perms_url = f"{organization.grafana_url}/api/access-control/user/permissions"
    assert perms_request.url == perms_url
    user_url = f"{organization.grafana_url}/api/user"
    assert user_request.url == user_url


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_grafana_authentication_token_created_older_grafana(make_organization):
    organization = make_organization(grafana_url="http://grafana.test")
    token_string = "glsa_the-token"

    headers = {
        "HTTP_AUTHORIZATION": token_string,
        "HTTP_X_GRAFANA_URL": organization.grafana_url,
    }
    request = APIRequestFactory().get("/", **headers)

    # setup Grafana API responses
    permissions = {"some-perm": "value"}
    # User API fails for older Grafana versions
    setup_service_account_api_mocks(organization.grafana_url, permissions, user_status=400)

    user, auth_token = GrafanaServiceAccountAuthentication().authenticate(request)

    assert user.is_service_account
    service_account = user.service_account
    assert service_account.organization == organization
    # use fallback data
    assert service_account.grafana_id == 0
    assert service_account.login == "grafana_service_account"
    assert auth_token.service_account == user.service_account


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_grafana_authentication_token_reuse_service_account(make_organization, make_service_account_for_organization):
    organization = make_organization(grafana_url="http://grafana.test")
    service_account = make_service_account_for_organization(organization)
    token_string = "glsa_the-token"

    headers = {
        "HTTP_AUTHORIZATION": token_string,
        "HTTP_X_GRAFANA_URL": organization.grafana_url,
    }
    request = APIRequestFactory().get("/", **headers)

    # setup Grafana API responses
    permissions = {"some-perm": "value"}
    user_data = {
        "login": service_account.login,
        "uid": f"service-account:{service_account.grafana_id}",
    }
    setup_service_account_api_mocks(organization.grafana_url, permissions, user_data)

    user, auth_token = GrafanaServiceAccountAuthentication().authenticate(request)

    assert user.is_service_account
    assert user.service_account == service_account
    assert auth_token.service_account == service_account


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_grafana_authentication_token_setup_org_if_missing(make_organization):
    grafana_url = "http://grafana.test"
    token_string = "glsa_the-token"

    headers = {
        "HTTP_AUTHORIZATION": token_string,
        "HTTP_X_GRAFANA_URL": grafana_url,
    }
    request = APIRequestFactory().get("/", **headers)

    # setup Grafana API responses
    permissions = {"some-perm": "value"}
    setup_service_account_api_mocks(grafana_url, permissions)

    request_sync_url = f"{grafana_url}/api/plugins/{PluginID.ONCALL}/resources/plugin/sync?wait=true&force=true"
    httpretty.register_uri(httpretty.POST, request_sync_url)

    assert Organization.objects.filter(grafana_url=grafana_url).count() == 0

    def sync_org():
        make_organization(grafana_url=grafana_url, is_rbac_permissions_enabled=True)
        return (True, {"status_code": 200})

    with patch("apps.grafana_plugin.helpers.client.GrafanaAPIClient.setup_organization") as mock_setup_org:
        mock_setup_org.side_effect = sync_org
        user, auth_token = GrafanaServiceAccountAuthentication().authenticate(request)

    mock_setup_org.assert_called_once()

    assert user.is_service_account
    service_account = user.service_account
    # organization is created
    organization = Organization.objects.filter(grafana_url=grafana_url).get()
    assert organization.grafana_url == grafana_url
    assert service_account.organization == organization
    assert auth_token.service_account == user.service_account
