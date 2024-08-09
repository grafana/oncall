import uuid
from unittest.mock import call, patch

import pytest

from apps.grafana_plugin.helpers.client import GcomAPIClient
from apps.grafana_plugin.helpers.gcom import get_instance_ids
from settings.base import CLOUD_LICENSE_NAME


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
        for _ in range(page_item_count):
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


@patch("apps.grafana_plugin.helpers.client.APIClient.api_get")
def test_get_instances_pagination_handles_streaming_errors_with_cursor_pagination(mock_api_get):
    query = GcomAPIClient.ACTIVE_INSTANCE_QUERY
    page_size = 10
    next_cursor1 = "abcd1234"
    next_cursor2 = "efgh5678"
    instance1 = {"id": "1"}
    instance2 = {"id": "2"}
    instance3 = {"id": "3"}

    mock_api_get.side_effect = [
        ({"items": [instance1], "nextCursor": next_cursor1}, {}),
        ({"items": [instance2]}, {}),  # failed request for the second page (missing nextCursor key)
        ({"items": [instance2], "nextCursor": next_cursor2}, {}),  # retried second page request has nextCursor key
        ({"items": [instance3], "nextCursor": None}, {}),  # last page
    ]
    client = GcomAPIClient("someToken")

    objects = []
    for page in client.get_instances(query, page_size):
        objects.extend(page["items"])

    assert instance1 in objects
    assert instance2 in objects
    assert instance3 in objects

    mock_api_get.assert_has_calls(
        [
            call(f"{query}&cursor=0&pageSize={page_size}"),  # 1st page
            call(f"{query}&cursor={next_cursor1}&pageSize={page_size}"),  # 2nd page, first try
            call(f"{query}&cursor={next_cursor1}&pageSize={page_size}"),  # 2nd page, retry
            call(f"{query}&cursor={next_cursor2}&pageSize={page_size}"),  # 3rd page
        ]
    )


@patch("apps.grafana_plugin.helpers.client.APIClient.api_get")
def test_get_instances_pagination_doesnt_infinitely_retry_on_streaming_errors(mock_api_get):
    query = GcomAPIClient.ACTIVE_INSTANCE_QUERY
    page_size = 10
    next_cursor1 = "abcd1234"
    instance1 = {"id": "1"}
    instance2 = {"id": "2"}

    mock_api_get.side_effect = [
        ({"items": [instance1], "nextCursor": next_cursor1}, {}),
        ({"items": [instance2]}, {}),  # failed request for the second page (missing nextCursor key)
        ({"items": [instance2]}, {}),  # 2nd failed request for the second page
        ({"items": [instance2]}, {}),  # 3rd failed request for the second page
        ({"items": [instance2]}, {}),  # 4th failed request for the second page
    ]
    client = GcomAPIClient("someToken")

    objects = []
    for page in client.get_instances(query, page_size):
        objects.extend(page["items"])

    assert instance1 in objects
    assert instance2 not in objects

    second_page_call = call(f"{query}&cursor={next_cursor1}&pageSize={page_size}")

    assert len(mock_api_get.mock_calls) == 5
    mock_api_get.assert_has_calls(
        [
            call(f"{query}&cursor=0&pageSize={page_size}"),  # 1st page
            second_page_call,  # 2nd page, 1st try
            second_page_call,  # 2nd page, 1st retry
            second_page_call,  # 2nd page, 2nd retry
            second_page_call,  # 2nd page, 3rd retry
        ]
    )


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


@pytest.mark.parametrize(
    "status, is_deleted",
    [
        ("deleted", True),
        ("active", False),
        ("deleting", False),
        ("paused", False),
        ("archived", False),
        ("archiving", False),
        ("restoring", False),
        ("migrating", False),
        ("migrated", False),
        ("suspending", False),
        ("suspended", False),
        ("pending", False),
        ("starting", False),
        ("unknown", False),
    ],
)
def test_cleanup_organization_deleted(status, is_deleted):
    client = GcomAPIClient("someToken")
    with patch.object(GcomAPIClient, "api_get", return_value=({"items": [{"status": status}]}, None)):
        assert client.is_stack_deleted("someStack") == is_deleted
