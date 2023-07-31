import uuid
from unittest.mock import patch

import pytest

from apps.grafana_plugin.helpers.client import GcomAPIClient
from apps.grafana_plugin.helpers.gcom import get_instance_ids
from settings.base import CLOUD_LICENSE_NAME


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


def build_paged_responses(page_size, pages, total_items):
    response = []
    remaining = total_items
    for i in range(pages):
        if not page_size:
            page_item_count = remaining
        else:
            page_item_count = min(page_size, remaining)
            remaining -= page_size

        items = []
        for j in range(page_item_count):
            items.append({"id": str(uuid.uuid4())})
        next_cursor = None if i == pages - 1 else i * page_size
        response.append(({"items": items, "nextCursor": next_cursor}, {}))
    return response


@pytest.mark.parametrize(
    "page_size, expected_pages, expected_items",
    [
        (None, 1, 0),
        (None, 1, 5),
        (10, 2, 20),
        (10, 4, 33),
    ],
)
def test_get_instances_pagination(page_size, expected_pages, expected_items):
    response = build_paged_responses(page_size, expected_pages, expected_items)
    client = GcomAPIClient("someToken")

    pages = []
    items = 0
    with patch(
        "apps.grafana_plugin.helpers.client.APIClient.api_get",
        side_effect=response,
    ):
        instance_pages = client.get_instances("", page_size)
        for page in instance_pages:
            pages.append(page)
            items += len(page.get("items", []))

    assert len(pages) == expected_pages
    assert items == expected_items


@pytest.mark.parametrize(
    "query, expected_pages, expected_items",
    [
        (GcomAPIClient.ACTIVE_INSTANCE_QUERY, 1, 0),
        ("", 1, 543),
        (GcomAPIClient.DELETED_INSTANCE_QUERY, 2, 2000),
        ("", 4, 3333),
    ],
)
def test_get_instance_ids_pagination(settings, query, expected_pages, expected_items):
    settings.GRAFANA_COM_API_TOKEN = "someToken"
    settings.LICENSE = CLOUD_LICENSE_NAME

    response = build_paged_responses(GcomAPIClient.PAGE_SIZE, expected_pages, expected_items)

    with patch(
        "apps.grafana_plugin.helpers.client.APIClient.api_get",
        side_effect=response,
    ):
        instance_ids, status = get_instance_ids(query)
        item_count = len(instance_ids)
        assert status is True
        assert item_count == expected_items
        if item_count > 0:
            assert type(next(iter(instance_ids))) is str
