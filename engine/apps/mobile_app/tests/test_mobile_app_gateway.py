import json
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.views import APIView

DOWNSTREAM_BACKEND = "incident"
MOCK_DOWNSTREAM_INCIDENT_API_URL = "https://mockdownstreamincidentapi.com"
MOCK_DOWNSTREAM_HEADERS = {"Authorization": "Bearer mock_jwt"}

MOCK_DOWNSTREAM_RESPONSE_DATA = {"foo": "bar"}


class MockResponse:
    def __init__(self, status_code=status.HTTP_200_OK, data=MOCK_DOWNSTREAM_RESPONSE_DATA):
        self.status_code = status_code
        self.data = data

    def json(self):
        return self.data


@pytest.mark.django_db
@patch("apps.mobile_app.views.requests")
@patch(
    "apps.mobile_app.views.MobileAppGatewayView._determine_grafana_incident_api_url",
    return_value=MOCK_DOWNSTREAM_INCIDENT_API_URL,
)
@patch("apps.mobile_app.views.MobileAppGatewayView._get_downstream_headers", return_value=MOCK_DOWNSTREAM_HEADERS)
@pytest.mark.parametrize("path", ["", "thing", "thing/123", "thing/123/otherthing", "thing/123/otherthing/456"])
def test_mobile_app_gateway_properly_proxies_paths(
    _mock_get_downstream_headers,
    _mock_determine_grafana_incident_api_url,
    mock_requests,
    make_organization_and_user_with_mobile_app_auth_token,
    path,
):
    mock_requests.post.return_value = MockResponse()

    _, _, auth_token = make_organization_and_user_with_mobile_app_auth_token()

    client = APIClient()
    url = reverse("mobile_app:gateway", kwargs={"downstream_backend": DOWNSTREAM_BACKEND, "downstream_path": path})

    response = client.post(url, HTTP_AUTHORIZATION=auth_token)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == MOCK_DOWNSTREAM_RESPONSE_DATA

    mock_requests.post.assert_called_once_with(
        f"{MOCK_DOWNSTREAM_INCIDENT_API_URL}/{path}",
        data={},
        params={},
        headers=MOCK_DOWNSTREAM_HEADERS,
    )


@pytest.mark.django_db
@patch("apps.mobile_app.views.requests")
@patch(
    "apps.mobile_app.views.MobileAppGatewayView._determine_grafana_incident_api_url",
    return_value=MOCK_DOWNSTREAM_INCIDENT_API_URL,
)
@patch("apps.mobile_app.views.MobileAppGatewayView._get_downstream_headers", return_value=MOCK_DOWNSTREAM_HEADERS)
@pytest.mark.parametrize("method", APIView.http_method_names)
def test_mobile_app_gateway_supports_all_methods(
    _mock_get_downstream_headers,
    _mock_determine_grafana_incident_api_url,
    mock_requests,
    make_organization_and_user_with_mobile_app_auth_token,
    method,
):
    mock_http_verb_method = getattr(mock_requests, method.lower())
    mock_http_verb_method.return_value = MockResponse()

    _, _, auth_token = make_organization_and_user_with_mobile_app_auth_token()

    client = APIClient()
    url = reverse("mobile_app:gateway", kwargs={"downstream_backend": DOWNSTREAM_BACKEND, "downstream_path": "test"})

    response = client.generic(method.upper(), url, HTTP_AUTHORIZATION=auth_token)
    assert response.status_code == status.HTTP_200_OK

    mock_http_verb_method.assert_called_once()


@pytest.mark.django_db
@patch("apps.mobile_app.views.requests")
@patch(
    "apps.mobile_app.views.MobileAppGatewayView._determine_grafana_incident_api_url",
    return_value=MOCK_DOWNSTREAM_INCIDENT_API_URL,
)
@patch("apps.mobile_app.views.MobileAppGatewayView._get_downstream_headers", return_value=MOCK_DOWNSTREAM_HEADERS)
def test_mobile_app_gateway_proxies_query_params(
    _mock_get_downstream_headers,
    _mock_determine_grafana_incident_api_url,
    mock_requests,
    make_organization_and_user_with_mobile_app_auth_token,
):
    path = "test/123"
    mock_requests.post.return_value = MockResponse()

    _, _, auth_token = make_organization_and_user_with_mobile_app_auth_token()

    client = APIClient()
    url = reverse("mobile_app:gateway", kwargs={"downstream_backend": DOWNSTREAM_BACKEND, "downstream_path": path})

    response = client.post(f"{url}?foo=bar&baz=hello", HTTP_AUTHORIZATION=auth_token)
    assert response.status_code == status.HTTP_200_OK

    mock_requests.post.assert_called_once_with(
        f"{MOCK_DOWNSTREAM_INCIDENT_API_URL}/{path}",
        data={},
        params={"foo": "bar", "baz": "hello"},
        headers=MOCK_DOWNSTREAM_HEADERS,
    )


@pytest.mark.django_db
@patch("apps.mobile_app.views.requests")
@patch(
    "apps.mobile_app.views.MobileAppGatewayView._determine_grafana_incident_api_url",
    return_value=MOCK_DOWNSTREAM_INCIDENT_API_URL,
)
@patch("apps.mobile_app.views.MobileAppGatewayView._get_downstream_headers", return_value=MOCK_DOWNSTREAM_HEADERS)
@pytest.mark.parametrize(
    "upstream_request_body",
    [
        None,
        {},
        {"vegetable": "potato", "fruit": "apple"},
    ],
)
def test_mobile_app_gateway_properly_proxies_request_body(
    _mock_get_downstream_headers,
    _mock_determine_grafana_incident_api_url,
    mock_requests,
    make_organization_and_user_with_mobile_app_auth_token,
    upstream_request_body,
):
    path = "test/123"
    mock_requests.post.return_value = MockResponse()

    _, _, auth_token = make_organization_and_user_with_mobile_app_auth_token()

    client = APIClient()
    url = reverse("mobile_app:gateway", kwargs={"downstream_backend": DOWNSTREAM_BACKEND, "downstream_path": path})

    response = client.post(
        url,
        data=json.dumps(upstream_request_body),
        content_type="application/json",
        HTTP_AUTHORIZATION=auth_token,
    )
    assert response.status_code == status.HTTP_200_OK

    mock_requests.post.assert_called_once_with(
        f"{MOCK_DOWNSTREAM_INCIDENT_API_URL}/{path}",
        data=upstream_request_body,
        params={},
        headers=MOCK_DOWNSTREAM_HEADERS,
    )


@pytest.mark.django_db
@patch("apps.mobile_app.views.requests")
@patch(
    "apps.mobile_app.views.MobileAppGatewayView._determine_grafana_incident_api_url",
    return_value=MOCK_DOWNSTREAM_INCIDENT_API_URL,
)
@patch("apps.mobile_app.views.MobileAppGatewayView._get_downstream_headers", return_value=MOCK_DOWNSTREAM_HEADERS)
@pytest.mark.parametrize(
    "downstream_backend,expected_status",
    [
        ("incident", status.HTTP_200_OK),
        ("foo", status.HTTP_404_NOT_FOUND),
    ],
)
def test_mobile_app_gateway_supported_downstream_backends(
    _mock_get_downstream_headers,
    _mock_determine_grafana_incident_api_url,
    mock_requests,
    make_organization_and_user_with_mobile_app_auth_token,
    downstream_backend,
    expected_status,
):
    mock_requests.post.return_value = MockResponse()

    _, _, auth_token = make_organization_and_user_with_mobile_app_auth_token()

    client = APIClient()
    url = reverse(
        "mobile_app:gateway", kwargs={"downstream_backend": downstream_backend, "downstream_path": "test/123"}
    )

    response = client.post(url, HTTP_AUTHORIZATION=auth_token)
    assert response.status_code == expected_status


@pytest.mark.django_db
@patch("apps.mobile_app.views.requests")
@patch(
    "apps.mobile_app.views.MobileAppGatewayView._determine_grafana_incident_api_url",
    return_value=MOCK_DOWNSTREAM_INCIDENT_API_URL,
)
@patch("apps.mobile_app.views.MobileAppGatewayView._get_downstream_headers", return_value=MOCK_DOWNSTREAM_HEADERS)
def test_mobile_app_gateway_mobile_app_auth_token(
    _mock_get_downstream_headers,
    _mock_determine_grafana_incident_api_url,
    mock_requests,
    make_organization_and_user_with_mobile_app_auth_token,
):
    mock_requests.post.return_value = MockResponse()

    _, _, auth_token = make_organization_and_user_with_mobile_app_auth_token()

    client = APIClient()
    url = reverse(
        "mobile_app:gateway", kwargs={"downstream_backend": DOWNSTREAM_BACKEND, "downstream_path": "test/123"}
    )

    response = client.post(url, HTTP_AUTHORIZATION="potato")
    assert response.status_code == status.HTTP_403_FORBIDDEN

    response = client.post(url, HTTP_AUTHORIZATION=auth_token)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
@patch("apps.mobile_app.views.requests")
@patch("apps.mobile_app.views.MobileAppGatewayView._get_downstream_headers", return_value=MOCK_DOWNSTREAM_HEADERS)
def test_mobile_app_gateway_incident_api_url(
    _mock_get_downstream_headers,
    mock_requests,
    make_organization_and_user_with_mobile_app_auth_token,
):
    mock_incident_backend_url = "https://mockincidentbackend.com"
    mock_requests.post.return_value = MockResponse()

    client = APIClient()
    url = reverse(
        "mobile_app:gateway", kwargs={"downstream_backend": DOWNSTREAM_BACKEND, "downstream_path": "test/123"}
    )

    # Grafana API returns None for the incident plugin settings
    with patch(
        "apps.mobile_app.views.GrafanaAPIClient.get_grafana_incident_plugin_settings"
    ) as mock_get_grafana_incident_plugin_settings:
        organization, _, auth_token = make_organization_and_user_with_mobile_app_auth_token()
        assert organization.grafana_incident_backend_url is None

        mock_get_grafana_incident_plugin_settings.return_value = (None, None)

        response = client.post(url, HTTP_AUTHORIZATION=auth_token)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Incident plugin settings jsonData doesn't contain the backend URL
    with patch(
        "apps.mobile_app.views.GrafanaAPIClient.get_grafana_incident_plugin_settings"
    ) as mock_get_grafana_incident_plugin_settings:
        organization, _, auth_token = make_organization_and_user_with_mobile_app_auth_token()
        assert organization.grafana_incident_backend_url is None

        mock_get_grafana_incident_plugin_settings.return_value = ({"jsonData": {}}, None)

        response = client.post(url, HTTP_AUTHORIZATION=auth_token)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Organization already has incident backend URL saved
    with patch(
        "apps.mobile_app.views.GrafanaAPIClient.get_grafana_incident_plugin_settings"
    ) as mock_get_grafana_incident_plugin_settings:
        organization, _, auth_token = make_organization_and_user_with_mobile_app_auth_token()
        organization.grafana_incident_backend_url = mock_incident_backend_url
        organization.save()

        response = client.post(url, HTTP_AUTHORIZATION=auth_token)
        assert response.status_code == status.HTTP_200_OK
        mock_get_grafana_incident_plugin_settings.assert_not_called()

    # Incident plugin settings jsonData contains the backend URL
    # check that it gets saved to the organization
    with patch(
        "apps.mobile_app.views.GrafanaAPIClient.get_grafana_incident_plugin_settings"
    ) as mock_get_grafana_incident_plugin_settings:
        organization, _, auth_token = make_organization_and_user_with_mobile_app_auth_token()
        assert organization.grafana_incident_backend_url is None

        mock_get_grafana_incident_plugin_settings.return_value = (
            {"jsonData": {"backendUrl": mock_incident_backend_url}},
            None,
        )

        response = client.post(url, HTTP_AUTHORIZATION=auth_token)
        assert response.status_code == status.HTTP_200_OK

        organization.refresh_from_db()
        assert organization.grafana_incident_backend_url == mock_incident_backend_url


# # TODO:
# @pytest.mark.django_db
# def test_mobile_app_gateway_downstream_jwt_auth(make_organization_and_user_with_mobile_app_auth_token):
#     _, _, auth_token = make_organization_and_user_with_mobile_app_auth_token()

#     client = APIClient()
#     url = reverse("mobile_app:gateway", kwargs={"downstream_backend": DOWNSTREAM_BACKEND, "downstream_path": "test"})

#     response = client.post(url, HTTP_AUTHORIZATION=auth_token)
#     assert response.status_code == status.HTTP_403_FORBIDDEN
