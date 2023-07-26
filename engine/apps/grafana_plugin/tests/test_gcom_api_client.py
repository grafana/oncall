from unittest.mock import patch

import pytest

from apps.grafana_plugin.helpers.client import GcomAPIClient


class TestIsRbacEnabledForStack:
    TEST_FEATURE_TOGGLE = "helloWorld"

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

    @pytest.mark.parametrize(
        "instance_info_feature_toggles,delimiter,expected",
        [
            ({}, " ", False),
            ({"enable": "foo,bar,baz"}, " ", False),
            ({"enable": "foo,bar,baz"}, ",", False),
            ({"enable": f"foo,bar,baz{TEST_FEATURE_TOGGLE}"}, " ", False),
            ({"enable": f"foo,bar,baz{TEST_FEATURE_TOGGLE}"}, ",", False),
            ({"enable": f"foo,bar,baz,{TEST_FEATURE_TOGGLE}abc"}, ",", False),
            ({"enable": f"foo,bar,baz,{TEST_FEATURE_TOGGLE}"}, ",", True),
        ],
    )
    def test_feature_is_enabled_via_enable_key(self, instance_info_feature_toggles, delimiter, expected) -> None:
        assert (
            GcomAPIClient("someFakeApiToken")._feature_is_enabled_via_enable_key(
                instance_info_feature_toggles, self.TEST_FEATURE_TOGGLE, delimiter
            )
            == expected
        )

    @pytest.mark.parametrize(
        "instance_info,expected",
        [
            ({}, False),
            ({"config": {}}, False),
            ({"config": {"feature_toggles": {}}}, False),
            ({"config": {"feature_toggles": {"enable": "foo,bar,baz"}}}, False),
            ({"config": {"feature_toggles": {TEST_FEATURE_TOGGLE: "false"}}}, False),
            ({"config": {"feature_toggles": {"enable": f"foo,bar,{TEST_FEATURE_TOGGLE}baz"}}}, False),
            ({"config": {"feature_toggles": {"enable": f"foo,bar,{TEST_FEATURE_TOGGLE},baz"}}}, True),
            ({"config": {"feature_toggles": {"enable": f"foo bar {TEST_FEATURE_TOGGLE} baz"}}}, True),
            ({"config": {"feature_toggles": {"enable": "foo bar baz", TEST_FEATURE_TOGGLE: "true"}}}, True),
            ({"config": {"feature_toggles": {TEST_FEATURE_TOGGLE: "true"}}}, True),
            # this case will probably never happen, but lets account for it anyways
            (
                {
                    "config": {
                        "feature_toggles": {
                            "enable": f"foo,bar,baz,{TEST_FEATURE_TOGGLE}",
                            TEST_FEATURE_TOGGLE: "false",
                        }
                    }
                },
                True,
            ),
        ],
    )
    def test_feature_toggle_is_enabled(self, instance_info, expected) -> None:
        assert (
            GcomAPIClient("someFakeApiToken")._feature_toggle_is_enabled(instance_info, self.TEST_FEATURE_TOGGLE)
            == expected
        )
