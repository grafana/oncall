import responses


def setup_service_account_api_mocks(grafana_url, perms=None, user_data=None, perms_status=200, user_status=200):
    # requires enabling responses
    if perms is None:
        perms = {}
    responses.add(responses.GET, f"{grafana_url}/api/access-control/user/permissions", json=perms, status=perms_status)

    if user_data is None:
        user_data = {"login": "some-login", "uid": "service-account:42"}
    responses.add(responses.GET, f"{grafana_url}/api/user", json=user_data, status=user_status)
