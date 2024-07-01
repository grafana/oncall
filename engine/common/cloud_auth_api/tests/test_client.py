import json

import httpretty
import pytest
from rest_framework import status

from common.cloud_auth_api.client import CloudAuthApiClient, CloudAuthApiException

GRAFANA_CLOUD_AUTH_API_URL = "http://example.com"
GRAFANA_CLOUD_AUTH_API_SYSTEM_TOKEN = "asdfasdfasdfasdf"


@pytest.fixture(autouse=True)
def configure_cloud_auth_api_client(settings):
    settings.GRAFANA_CLOUD_AUTH_API_URL = GRAFANA_CLOUD_AUTH_API_URL
    settings.GRAFANA_CLOUD_AUTH_API_SYSTEM_TOKEN = GRAFANA_CLOUD_AUTH_API_SYSTEM_TOKEN


@pytest.mark.django_db
@pytest.mark.parametrize("response_status_code", [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED])
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_request_signed_token(make_organization, make_user_for_organization, response_status_code):
    mock_auth_token = ",mnasdlkjlakjoqwejroiqwejr"
    mock_response_text = "error message"

    org_id = 1
    stack_id = 5

    organization = make_organization(stack_id=stack_id, org_id=org_id)
    user = make_user_for_organization(organization=organization)

    scopes = ["incident:write", "foo:bar"]
    extra_claims = {"vegetable": "carrot", "fruit": "apple"}

    def _make_request():
        return CloudAuthApiClient().request_signed_token(user, scopes, extra_claims)

    url = f"{GRAFANA_CLOUD_AUTH_API_URL}/v1/sign"
    mock_response = httpretty.Response(json.dumps({"data": {"token": mock_auth_token}}), status=response_status_code)
    httpretty.register_uri(httpretty.POST, url, responses=[mock_response])

    if response_status_code != status.HTTP_200_OK:
        with pytest.raises(CloudAuthApiException) as excinfo:
            _make_request()

            assert excinfo.value.status == response_status_code
            assert excinfo.value.method == "POST"
            assert excinfo.value.msg == mock_response_text
            assert excinfo.value.url == url
    else:
        assert _make_request() == mock_auth_token

    last_request = httpretty.last_request()
    assert last_request.method == "POST"
    assert last_request.url == url

    # assert we're sending the right body
    assert json.loads(last_request.body) == {
        "claims": {
            "sub": f"email:{user.email}",
        },
        "extra": extra_claims,
        "accessPolicy": {
            "scopes": scopes,
        },
    }

    # assert we're sending the right headers
    assert last_request.headers["Authorization"] == f"Bearer {GRAFANA_CLOUD_AUTH_API_SYSTEM_TOKEN}"
    assert last_request.headers["X-Org-ID"] == str(org_id)
    assert last_request.headers["X-Realms"] == json.dumps(
        [
            {
                "type": "stack",
                "identifier": str(stack_id),
            },
        ]
    )
