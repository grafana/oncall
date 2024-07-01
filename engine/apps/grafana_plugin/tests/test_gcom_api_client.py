import uuid
from unittest.mock import patch

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
