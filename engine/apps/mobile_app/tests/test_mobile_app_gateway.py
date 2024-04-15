import json
from unittest.mock import patch

import pytest
import requests
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.views import APIView

from apps.mobile_app.views import MobileAppGatewayView
from common.cloud_auth_api.client import CloudAuthApiClient, CloudAuthApiException

DOWNSTREAM_BACKEND = "incident"
MOCK_DOWNSTREAM_URL = "https://mockdownstream.com"
MOCK_DOWNSTREAM_INCIDENT_API_URL = "https://mockdownstreamincidentapi.com"
MOCK_DOWNSTREAM_HEADERS = {"Authorization": "Bearer mock_auth_token"}
MOCK_DOWNSTREAM_RESPONSE_DATA = {"foo": "bar"}

MOCK_AUTH_TOKEN = "mncn,zxcnv,mznxcv"


@pytest.fixture(autouse=True)
def enable_mobile_app_gateway(settings):
    settings.MOBILE_APP_GATEWAY_ENABLED = True
    settings.GRAFANA_CLOUD_AUTH_API_URL = "asdfasdf"
    settings.GRAFANA_CLOUD_AUTH_API_SYSTEM_TOKEN = "zxcvzx"


class MockResponse:
    def __init__(self, status_code=status.HTTP_200_OK, data=MOCK_DOWNSTREAM_RESPONSE_DATA):
        self.status_code = status_code
        self.data = data

    def json(self):
        return self.data


@pytest.mark.django_db
@patch("apps.mobile_app.views.requests")
@patch("apps.mobile_app.views.MobileAppGatewayView._get_downstream_headers", return_value=MOCK_DOWNSTREAM_HEADERS)
@pytest.mark.parametrize("path", ["", "thing", "thing/123", "thing/123/otherthing", "thing/123/otherthing/456"])
def test_mobile_app_gateway_properly_proxies_paths(
    _mock_get_downstream_headers,
    mock_requests,
    make_organization_and_user_with_mobile_app_auth_token,
    path,
):
    mock_requests.post.return_value = MockResponse()

    org, _, auth_token = make_organization_and_user_with_mobile_app_auth_token()
    org.grafana_incident_backend_url = MOCK_DOWNSTREAM_INCIDENT_API_URL
    org.save()

    client = APIClient()
    url = reverse("mobile_app:gateway", kwargs={"downstream_backend": DOWNSTREAM_BACKEND, "downstream_path": path})

    response = client.post(url, HTTP_AUTHORIZATION=auth_token)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == MOCK_DOWNSTREAM_RESPONSE_DATA

    mock_requests.post.assert_called_once_with(
        f"{MOCK_DOWNSTREAM_INCIDENT_API_URL}/{path}",
        data=b"",
        params={},
        headers=MOCK_DOWNSTREAM_HEADERS,
    )


@pytest.mark.django_db
@patch("apps.mobile_app.views.requests")
@patch("apps.mobile_app.views.MobileAppGatewayView._get_downstream_url", return_value=MOCK_DOWNSTREAM_URL)
@patch("apps.mobile_app.views.MobileAppGatewayView._get_downstream_headers", return_value=MOCK_DOWNSTREAM_HEADERS)
@pytest.mark.parametrize("method", APIView.http_method_names)
def test_mobile_app_gateway_supports_all_methods(
    _mock_get_downstream_headers,
    _mock_get_downstream_url,
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
@patch("apps.mobile_app.views.MobileAppGatewayView._get_downstream_url", return_value=MOCK_DOWNSTREAM_URL)
@patch("apps.mobile_app.views.MobileAppGatewayView._get_downstream_headers", return_value=MOCK_DOWNSTREAM_HEADERS)
def test_mobile_app_gateway_proxies_query_params(
    _mock_get_downstream_headers,
    _mock_get_downstream_url,
    mock_requests,
    make_organization_and_user_with_mobile_app_auth_token,
):
    mock_requests.post.return_value = MockResponse()

    _, _, auth_token = make_organization_and_user_with_mobile_app_auth_token()

    client = APIClient()
    url = reverse("mobile_app:gateway", kwargs={"downstream_backend": DOWNSTREAM_BACKEND, "downstream_path": "test"})

    response = client.post(f"{url}?foo=bar&baz=hello", HTTP_AUTHORIZATION=auth_token)
    assert response.status_code == status.HTTP_200_OK

    mock_requests.post.assert_called_once_with(
        MOCK_DOWNSTREAM_URL,
        data=b"",
        params={"foo": "bar", "baz": "hello"},
        headers=MOCK_DOWNSTREAM_HEADERS,
    )


@pytest.mark.django_db
@patch("apps.mobile_app.views.requests")
@patch("apps.mobile_app.views.MobileAppGatewayView._get_downstream_url", return_value=MOCK_DOWNSTREAM_URL)
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
    _mock_get_downstream_url,
    mock_requests,
    make_organization_and_user_with_mobile_app_auth_token,
    upstream_request_body,
):
    mock_requests.post.return_value = MockResponse()

    _, _, auth_token = make_organization_and_user_with_mobile_app_auth_token()

    client = APIClient()
    url = reverse("mobile_app:gateway", kwargs={"downstream_backend": DOWNSTREAM_BACKEND, "downstream_path": "test"})
    data = json.dumps(upstream_request_body)

    response = client.post(
        url,
        data=data,
        content_type="application/json",
        HTTP_AUTHORIZATION=auth_token,
    )
    assert response.status_code == status.HTTP_200_OK

    mock_requests.post.assert_called_once_with(
        MOCK_DOWNSTREAM_URL,
        data=data.encode("utf-8"),
        params={},
        headers=MOCK_DOWNSTREAM_HEADERS,
    )


@pytest.mark.django_db
@patch("apps.mobile_app.views.requests")
@patch("apps.mobile_app.views.MobileAppGatewayView._get_downstream_url", return_value=MOCK_DOWNSTREAM_URL)
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
    _mock_get_downstream_url,
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
@patch("apps.mobile_app.views.requests.post")
@patch("apps.mobile_app.views.MobileAppGatewayView._get_downstream_url", return_value=MOCK_DOWNSTREAM_URL)
@patch("apps.mobile_app.views.MobileAppGatewayView._get_downstream_headers", return_value=MOCK_DOWNSTREAM_HEADERS)
@pytest.mark.parametrize(
    "ExceptionClass,exception_args,expected_status",
    [
        (requests.exceptions.ConnectionError, (), status.HTTP_502_BAD_GATEWAY),
        (requests.exceptions.HTTPError, (), status.HTTP_502_BAD_GATEWAY),
        (requests.exceptions.TooManyRedirects, (), status.HTTP_502_BAD_GATEWAY),
        (requests.exceptions.Timeout, (), status.HTTP_502_BAD_GATEWAY),
        (requests.exceptions.JSONDecodeError, ("", "", 5), status.HTTP_400_BAD_REQUEST),
        (CloudAuthApiException, (403, "http://example.com"), status.HTTP_502_BAD_GATEWAY),
    ],
)
def test_mobile_app_gateway_catches_errors_from_downstream_server(
    _mock_get_downstream_headers,
    _mock_get_downstream_url,
    mock_requests_post,
    make_organization_and_user_with_mobile_app_auth_token,
    ExceptionClass,
    exception_args,
    expected_status,
):
    def _raise_exception(*args, **kwargs):
        raise ExceptionClass(*exception_args)

    mock_requests_post.side_effect = _raise_exception

    _, _, auth_token = make_organization_and_user_with_mobile_app_auth_token()

    client = APIClient()
    url = reverse("mobile_app:gateway", kwargs={"downstream_backend": DOWNSTREAM_BACKEND, "downstream_path": "test"})

    response = client.post(url, HTTP_AUTHORIZATION=auth_token)
    assert response.status_code == expected_status


@pytest.mark.django_db
@patch("apps.mobile_app.views.requests")
@patch("apps.mobile_app.views.MobileAppGatewayView._get_downstream_url", return_value=MOCK_DOWNSTREAM_URL)
@patch("apps.mobile_app.views.MobileAppGatewayView._get_downstream_headers", return_value=MOCK_DOWNSTREAM_HEADERS)
def test_mobile_app_gateway_mobile_app_auth_token(
    _mock_get_downstream_headers,
    _mock_get_downstream_url,
    mock_requests,
    make_organization_and_user_with_mobile_app_auth_token,
):
    mock_requests.post.return_value = MockResponse()

    _, _, auth_token = make_organization_and_user_with_mobile_app_auth_token()

    client = APIClient()
    url = reverse("mobile_app:gateway", kwargs={"downstream_backend": DOWNSTREAM_BACKEND, "downstream_path": "test"})

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
    url = reverse("mobile_app:gateway", kwargs={"downstream_backend": DOWNSTREAM_BACKEND, "downstream_path": "test"})

    # Organization has no incident backend URL saved
    organization, _, auth_token = make_organization_and_user_with_mobile_app_auth_token()
    assert organization.grafana_incident_backend_url is None

    response = client.post(url, HTTP_AUTHORIZATION=auth_token)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Organization already has incident backend URL saved
    organization, _, auth_token = make_organization_and_user_with_mobile_app_auth_token()
    organization.grafana_incident_backend_url = mock_incident_backend_url
    organization.save()

    response = client.post(url, HTTP_AUTHORIZATION=auth_token)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
@patch("apps.mobile_app.views.requests")
@patch("apps.mobile_app.views.MobileAppGatewayView._get_auth_token", return_value=MOCK_AUTH_TOKEN)
@patch("apps.mobile_app.views.MobileAppGatewayView._get_downstream_url", return_value=MOCK_DOWNSTREAM_URL)
def test_mobile_app_gateway_proxies_headers(
    _mock_get_downstream_url,
    _mock_get_auth_token,
    mock_requests,
    make_organization_and_user_with_mobile_app_auth_token,
):
    mock_requests.post.return_value = MockResponse()

    _, _, auth_token = make_organization_and_user_with_mobile_app_auth_token()

    client = APIClient()
    url = reverse("mobile_app:gateway", kwargs={"downstream_backend": DOWNSTREAM_BACKEND, "downstream_path": "test"})

    content_type_header = "foo/bar"
    response = client.post(url, HTTP_AUTHORIZATION=auth_token, headers={"Content-Type": content_type_header})
    assert response.status_code == status.HTTP_200_OK

    mock_requests.post.assert_called_once_with(
        MOCK_DOWNSTREAM_URL,
        data=b"",
        params={},
        headers={
            "Authorization": f"Bearer {MOCK_AUTH_TOKEN}",
            "Content-Type": content_type_header,
        },
    )


@pytest.mark.django_db
@patch("apps.mobile_app.views.CloudAuthApiClient.request_signed_token", return_value=MOCK_AUTH_TOKEN)
def test_mobile_app_gateway_properly_generates_an_auth_token(
    mock_request_signed_token,
    make_organization,
    make_user_for_organization,
):
    stack_id = 895
    organization = make_organization(stack_id=stack_id)
    user = make_user_for_organization(organization)

    auth_token = MobileAppGatewayView._get_auth_token(DOWNSTREAM_BACKEND, user)

    assert auth_token == f"{stack_id}:{MOCK_AUTH_TOKEN}"
    mock_request_signed_token.assert_called_once_with(user, [CloudAuthApiClient.Scopes.INCIDENT_WRITE])
