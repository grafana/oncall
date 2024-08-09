from unittest.mock import patch

import pytest
from rest_framework import status

from apps.grafana_plugin.helpers.client import GrafanaAPIClient

API_URL = "/foo/bar"
API_TOKEN = "dfjkfdjkfd"


class TestGetUsersPermissions:
    @pytest.mark.parametrize("api_response_data", [None, []])
    @patch("apps.grafana_plugin.helpers.client.GrafanaAPIClient.api_get")
    def test_api_call_returns_none_or_list(self, mocked_grafana_api_client_api_get, api_response_data):
        mocked_grafana_api_client_api_get.return_value = (api_response_data, "dfkjfdkj")
        api_client = GrafanaAPIClient(API_URL, API_TOKEN)
        assert api_client.get_users_permissions() is None

    @patch("apps.grafana_plugin.helpers.client.GrafanaAPIClient.api_get")
    def test_it_properly_transforms_the_data(self, mocked_grafana_api_client_api_get):
        mocked_grafana_api_client_api_get.return_value = (
            {"1": {"grafana-oncall-app.alert-groups:read": [""], "grafana-oncall-app.alert-groups:write": [""]}},
            "asdfasdf",
        )

        api_client = GrafanaAPIClient(API_URL, API_TOKEN)

        permissions = api_client.get_users_permissions()
        assert permissions == {
            "1": [
                {"action": "grafana-oncall-app.alert-groups:read"},
                {"action": "grafana-oncall-app.alert-groups:write"},
            ]
        }


class TestGetUsers:
    @pytest.mark.parametrize(
        "rbac_is_enabled,api_get_return_value,get_users_permissions_return_value,expected",
        [
            # RBAC is enabled - permissions are returned
            (
                True,
                [
                    {"userId": 1, "foo": "bar"},
                    {"userId": 2, "foo": "baz"},
                ],
                {
                    "1": [
                        {"action": "grafana-oncall-app.alert-groups:read"},
                        {"action": "grafana-oncall-app.alert-groups:write"},
                    ],
                },
                [
                    {
                        "userId": 1,
                        "foo": "bar",
                        "permissions": [
                            {"action": "grafana-oncall-app.alert-groups:read"},
                            {"action": "grafana-oncall-app.alert-groups:write"},
                        ],
                    },
                    {
                        "userId": 2,
                        "foo": "baz",
                        "permissions": [],
                    },
                ],
            ),
            # RBAC is enabled - permissions endpoint returns no permissions (ex. HTTP 500)
            (
                True,
                [
                    {"userId": 1, "foo": "bar"},
                    {"userId": 2, "foo": "baz"},
                ],
                None,
                [],
            ),
            # RBAC is not enabled - we don't fetch permissions (hence don't care about its response)
            (
                False,
                [
                    {"userId": 1, "foo": "bar"},
                    {"userId": 2, "foo": "baz"},
                ],
                None,
                [
                    {"userId": 1, "foo": "bar", "permissions": []},
                    {
                        "userId": 2,
                        "foo": "baz",
                        "permissions": [],
                    },
                ],
            ),
        ],
    )
    @patch("apps.grafana_plugin.helpers.client.GrafanaAPIClient.api_get")
    @patch("apps.grafana_plugin.helpers.client.GrafanaAPIClient.get_users_permissions")
    def test_it_returns_none_if_permissions_call_returns_none(
        self,
        mocked_grafana_api_client_get_users_permissions,
        mocked_grafana_api_client_api_get,
        rbac_is_enabled,
        api_get_return_value,
        get_users_permissions_return_value,
        expected,
    ):
        mocked_grafana_api_client_api_get.return_value = (api_get_return_value, "dfjkfdjkfd")
        mocked_grafana_api_client_get_users_permissions.return_value = get_users_permissions_return_value
        api_client = GrafanaAPIClient(API_URL, API_TOKEN)
        assert api_client.get_users(rbac_is_enabled) == expected


class TestIsRbacEnabledForOrganization:
    @pytest.mark.parametrize(
        "api_response_connected,api_status_code,expected",
        [
            (True, status.HTTP_200_OK, (True, False)),
            (False, status.HTTP_404_NOT_FOUND, (False, False)),
            (False, status.HTTP_503_SERVICE_UNAVAILABLE, (False, True)),
        ],
    )
    @patch("apps.grafana_plugin.helpers.client.GrafanaAPIClient.api_head")
    def test_it_returns_based_on_status_code_of_head_call(
        self, mocked_grafana_api_client_api_head, api_response_connected, api_status_code, expected
    ):
        mocked_grafana_api_client_api_head.return_value = (None, {"connected": api_response_connected})
        mocked_grafana_api_client_api_head.return_value = (
            None,
            {"connected": api_response_connected, "status_code": api_status_code},
        )

        api_client = GrafanaAPIClient(API_URL, API_TOKEN)
        assert api_client.is_rbac_enabled_for_organization() == expected
