import json
from unittest.mock import patch

import pytest
import requests
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.views import APIView

from apps.mobile_app.views import MobileAppGatewayView

DOWNSTREAM_BACKEND = "incident"
MOCK_DOWNSTREAM_URL = "https://mockdownstream.com"
MOCK_DOWNSTREAM_INCIDENT_API_URL = "https://mockdownstreamincidentapi.com"
MOCK_DOWNSTREAM_HEADERS = {"Authorization": "Bearer mock_jwt"}
MOCK_DOWNSTREAM_RESPONSE_DATA = {"foo": "bar"}

MOCK_TIMEZONE_NOW = timezone.datetime(2021, 1, 1, 3, 4, 5, tzinfo=timezone.utc)
MOCK_JWT = "mncn,zxcnv,mznxcv"
MOCK_JWT_PRIVATE_KEY = "asd,mzcxn,vmnzxcv,mnzx,cvmnzaslkdjflaksjdf"


@pytest.fixture(autouse=True)
def enable_mobile_app_gateway(settings):
    settings.MOBILE_APP_GATEWAY_ENABLED = True
    settings.MOBILE_APP_GATEWAY_RSA_PRIVATE_KEY = MOCK_JWT_PRIVATE_KEY


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
        data={},
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
        data={},
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

    response = client.post(
        url,
        data=json.dumps(upstream_request_body),
        content_type="application/json",
        HTTP_AUTHORIZATION=auth_token,
    )
    assert response.status_code == status.HTTP_200_OK

    mock_requests.post.assert_called_once_with(
        MOCK_DOWNSTREAM_URL,
        data=upstream_request_body,
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
@patch("apps.mobile_app.views.MobileAppGatewayView._construct_jwt", return_value=MOCK_JWT)
@patch("apps.mobile_app.views.MobileAppGatewayView._get_downstream_url", return_value=MOCK_DOWNSTREAM_URL)
def test_mobile_app_gateway_jwt_header(
    _mock_get_downstream_url,
    _mock_construct_jwt,
    mock_requests,
    make_organization_and_user_with_mobile_app_auth_token,
):
    mock_requests.post.return_value = MockResponse()

    _, _, auth_token = make_organization_and_user_with_mobile_app_auth_token()

    client = APIClient()
    url = reverse("mobile_app:gateway", kwargs={"downstream_backend": DOWNSTREAM_BACKEND, "downstream_path": "test"})

    response = client.post(url, HTTP_AUTHORIZATION=auth_token)
    assert response.status_code == status.HTTP_200_OK

    mock_requests.post.assert_called_once_with(
        MOCK_DOWNSTREAM_URL,
        data={},
        params={},
        headers={"Authorization": f"Bearer {MOCK_JWT}"},
    )


@pytest.mark.django_db
@patch("apps.mobile_app.views.jwt.encode", return_value=MOCK_JWT)
@patch("apps.mobile_app.views.timezone.now", return_value=MOCK_TIMEZONE_NOW)
def test_mobile_app_gateway_properly_generates_a_jwt(
    _mock_timezone_now,
    mock_jwt_encode,
    make_organization,
    make_user_for_organization,
):
    user_id = 90095905
    stack_id = 895
    organization_id = 8905
    stack_slug = "mvcmnvcmnvc"
    org_slug = "raintank"

    organization = make_organization(
        stack_id=stack_id, org_id=organization_id, stack_slug=stack_slug, org_slug=org_slug
    )
    user = make_user_for_organization(organization, user_id=user_id)

    encoded_jwt = MobileAppGatewayView._construct_jwt(user)

    assert encoded_jwt == MOCK_JWT
    mock_jwt_encode.assert_called_once_with(
        {
            "iat": MOCK_TIMEZONE_NOW,
            "exp": MOCK_TIMEZONE_NOW + timezone.timedelta(minutes=1),
            "user_id": user.user_id,  # grafana user ID
            "stack_id": organization.stack_id,
            "organization_id": organization.org_id,  # grafana org ID
            "stack_slug": organization.stack_slug,
            "org_slug": organization.org_slug,
        },
        MOCK_JWT_PRIVATE_KEY,
        algorithm="RS256",
    )
