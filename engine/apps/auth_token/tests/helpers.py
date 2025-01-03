import json

import httpretty


def setup_service_account_api_mocks(grafana_url, perms=None, user_data=None, perms_status=200, user_status=200):
    # requires enabling httpretty
    if perms is None:
        perms = {}
    mock_response = httpretty.Response(status=perms_status, body=json.dumps(perms))
    perms_url = f"{grafana_url}/api/access-control/user/permissions"
    httpretty.register_uri(httpretty.GET, perms_url, responses=[mock_response])

    if user_data is None:
        user_data = {"login": "some-login", "uid": "service-account:42"}
    mock_response = httpretty.Response(status=user_status, body=json.dumps(user_data))
    user_url = f"{grafana_url}/api/user"
    httpretty.register_uri(httpretty.GET, user_url, responses=[mock_response])
