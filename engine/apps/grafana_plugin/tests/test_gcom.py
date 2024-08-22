from unittest.mock import patch

import pytest

from apps.grafana_plugin.helpers.gcom import check_gcom_permission


@pytest.mark.django_db
def test_check_gcom_permission_updates_fields(make_organization):
    gcom_token = "gcom:test_token"
    fixed_token = "fixed_token"
    instance_info = {
        "id": 324534,
        "slug": "testinstance",
        "url": "http://example.com",
        "orgId": 5671,
        "orgSlug": "testorg",
        "orgName": "Test Org",
        "regionSlug": "us",
        "clusterSlug": "us-test",
    }
    context = {
        "stack_id": str(instance_info["id"]),
        "org_id": str(instance_info["orgId"]),
        "grafana_token": fixed_token,
    }

    org = make_organization(stack_id=instance_info["id"], org_id=instance_info["orgId"], api_token="broken_token")

    with patch(
        "apps.grafana_plugin.helpers.GcomAPIClient.get_instance_info",
        return_value=instance_info,
    ) as mock_instance_info:
        check_gcom_permission(gcom_token, context)
        mock_instance_info.assert_called()

    org.refresh_from_db()
    assert org.stack_id == instance_info["id"]
    assert org.stack_slug == instance_info["slug"]
    assert org.grafana_url == instance_info["url"]
    assert org.org_id == instance_info["orgId"]
    assert org.org_slug == instance_info["orgSlug"]
    assert org.org_title == instance_info["orgName"]
    assert org.region_slug == instance_info["regionSlug"]
    assert org.cluster_slug == instance_info["clusterSlug"]
    assert org.api_token == fixed_token
    assert org.gcom_token == gcom_token
