from unittest.mock import patch

import pytest

from apps.grafana_plugin.helpers.client import GcomAPIClient


class TestIsRbacEnabledForOrganization:
    @pytest.mark.parametrize(
        "gcom_api_response,expected",
        [
            (None, False),
            ({}, False),
            ({"config": {}}, False),
            ({"config": {"feature_toggles": {}}}, False),
            ({"config": {"feature_toggles": {"accessControlOnCall": "false"}}}, False),
            ({"config": {"feature_toggles": {"accessControlOnCall": "true"}}}, True),
        ],
    )
    @patch("apps.grafana_plugin.helpers.client.GcomAPIClient.api_get")
    def test_it_returns_based_on_feature_toggle_value(
        self, mocked_gcom_api_client_api_get, gcom_api_response, expected
    ):
        stack_id = 5
        mocked_gcom_api_client_api_get.return_value = (gcom_api_response, {"status_code": 200})

        api_client = GcomAPIClient("someFakeApiToken")
        assert api_client.is_rbac_enabled_for_stack(stack_id) == expected
        assert mocked_gcom_api_client_api_get.called_once_with(f"instances/{stack_id}?config=true")
