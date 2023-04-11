from unittest.mock import patch

import pytest

from apps.grafana_plugin.helpers.client import GrafanaAPIClient

API_URL = "/foo/bar"
API_TOKEN = "dfjkfdjkfd"


class TestGetUsersPermissions:
    def test_rbac_is_not_enabled_for_org(self):
        api_client = GrafanaAPIClient(API_URL, API_TOKEN)
        permissions = api_client.get_users_permissions(False)
        assert len(permissions.keys()) == 0

    @patch("apps.grafana_plugin.helpers.client.GrafanaAPIClient.api_get")
    def test_api_call_returns_none(self, mocked_grafana_api_client_api_get):
        mocked_grafana_api_client_api_get.return_value = (None, "dfkjfdkj")

        api_client = GrafanaAPIClient(API_URL, API_TOKEN)

        permissions = api_client.get_users_permissions(True)
        assert len(permissions.keys()) == 0

    @patch("apps.grafana_plugin.helpers.client.GrafanaAPIClient.api_get")
    def test_it_properly_transforms_the_data(self, mocked_grafana_api_client_api_get):
        mocked_grafana_api_client_api_get.return_value = (
            {"1": {"grafana-oncall-app.alert-groups:read": [""], "grafana-oncall-app.alert-groups:write": [""]}},
            "asdfasdf",
        )

        api_client = GrafanaAPIClient(API_URL, API_TOKEN)

        permissions = api_client.get_users_permissions(True)
        assert permissions == {
            "1": [
                {"action": "grafana-oncall-app.alert-groups:read"},
                {"action": "grafana-oncall-app.alert-groups:write"},
            ]
        }


class TestIsRbacEnabledForOrganization:
    @pytest.mark.parametrize(
        "api_response_connected,expected",
        [
            (True, True),
            (False, False),
        ],
    )
    @patch("apps.grafana_plugin.helpers.client.GrafanaAPIClient.api_head")
    def test_it_returns_based_on_status_code_of_head_call(
        self, mocked_grafana_api_client_api_head, api_response_connected, expected
    ):
        mocked_grafana_api_client_api_head.return_value = (None, {"connected": api_response_connected})

        api_client = GrafanaAPIClient(API_URL, API_TOKEN)
        assert api_client.is_rbac_enabled_for_organization() == expected
