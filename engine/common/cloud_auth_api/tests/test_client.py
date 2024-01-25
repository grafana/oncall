from unittest.mock import patch

import pytest
from rest_framework import status

from common.cloud_auth_api.client import CloudAuthApiClient, CloudAuthApiException

GRAFANA_CLOUD_AUTH_API_URL = "http://example.com"
GRAFANA_CLOUD_AUTH_API_SYSTEM_TOKEN = "asdfasdfasdfasdf"


@pytest.fixture(autouse=True)
def configure_cloud_auth_api_client(settings):
    settings.GRAFANA_CLOUD_AUTH_API_URL = GRAFANA_CLOUD_AUTH_API_URL
    settings.GRAFANA_CLOUD_AUTH_API_SYSTEM_TOKEN = GRAFANA_CLOUD_AUTH_API_SYSTEM_TOKEN


@patch("common.cloud_auth_api.client.requests")
@pytest.mark.parametrize("response_status_code", [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED])
def test_request_signed_token(mock_requests, response_status_code):
    mock_auth_token = ",mnasdlkjlakjoqwejroiqwejr"
    mock_response_text = "error message"

    org_id = 1
    stack_id = 5
    scopes = ["incident:write", "foo:bar"]
    claims = {"vegetable": "carrot", "fruit": "apple"}

    class MockResponse:
        text = mock_response_text

        def __init__(self, status_code):
            self.status_code = status_code

        def json(self):
            return {
                "data": {
                    "token": mock_auth_token,
                },
            }

    mock_requests.post.return_value = MockResponse(response_status_code)

    def _make_request():
        return CloudAuthApiClient().request_signed_token(org_id, stack_id, scopes, claims)

    url = f"{GRAFANA_CLOUD_AUTH_API_URL}/v1/sign"

    if response_status_code != status.HTTP_200_OK:
        with pytest.raises(CloudAuthApiException) as excinfo:
            _make_request()

            assert excinfo.value.status == response_status_code
            assert excinfo.value.method == "POST"
            assert excinfo.value.msg == mock_response_text
            assert excinfo.value.url == url
    else:
        assert _make_request() == mock_auth_token

    mock_requests.post.assert_called_once_with(
        url,
        headers={
            "Authorization": f"Bearer {GRAFANA_CLOUD_AUTH_API_SYSTEM_TOKEN}",
            "X-Org-ID": org_id,
            "X-Realms": [
                {
                    "type": "stack",
                    "identifier": stack_id,
                },
            ],
        },
        json={
            "claims": claims,
            "extra": {
                "scopes": scopes,
                "org_id": org_id,
            },
        },
    )
