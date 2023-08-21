import pytest
from django.core.cache import cache

from apps.metrics_exporter.constants import (
    ALERT_GROUPS_RESPONSE_TIME,
    ALERT_GROUPS_TOTAL,
    USER_WAS_NOTIFIED_OF_ALERT_GROUPS,
)
from apps.metrics_exporter.helpers import (
    get_metric_alert_groups_response_time_key,
    get_metric_alert_groups_total_key,
    get_metric_user_was_notified_of_alert_groups_key,
)

METRICS_TEST_INTEGRATION_NAME = "Test integration"
METRICS_TEST_ORG_ID = 123  # random number
METRICS_TEST_INSTANCE_SLUG = "test_instance"
METRICS_TEST_INSTANCE_ID = 292  # random number
METRICS_TEST_USER_USERNAME = "Alex"


@pytest.fixture()
def mock_cache_get_metrics_for_collector(monkeypatch):
    def _mock_cache_get(key, *args, **kwargs):
        if key.startswith(ALERT_GROUPS_TOTAL):
            key = ALERT_GROUPS_TOTAL
        elif key.startswith(ALERT_GROUPS_RESPONSE_TIME):
            key = ALERT_GROUPS_RESPONSE_TIME
        elif key.startswith(USER_WAS_NOTIFIED_OF_ALERT_GROUPS):
            key = USER_WAS_NOTIFIED_OF_ALERT_GROUPS
        test_metrics = {
            ALERT_GROUPS_TOTAL: {
                1: {
                    "integration_name": "Test metrics integration",
                    "team_name": "Test team",
                    "team_id": 1,
                    "org_id": 1,
                    "slug": "Test stack",
                    "id": 1,
                    "firing": 2,
                    "acknowledged": 3,
                    "silenced": 4,
                    "resolved": 5,
                }
            },
            ALERT_GROUPS_RESPONSE_TIME: {
                1: {
                    "integration_name": "Test metrics integration",
                    "team_name": "Test team",
                    "team_id": 1,
                    "org_id": 1,
                    "slug": "Test stack",
                    "id": 1,
                    "response_time": [2, 10, 200, 650],
                }
            },
            USER_WAS_NOTIFIED_OF_ALERT_GROUPS: {
                1: {
                    "org_id": 1,
                    "slug": "Test stack",
                    "id": 1,
                    "user_username": "Alex",
                    "counter": 4,
                }
            },
        }
        return test_metrics.get(key)

    def _mock_cache_get_many(keys, *args, **kwargs):
        return {key: _mock_cache_get(key) for key in keys if _mock_cache_get(key)}

    monkeypatch.setattr(cache, "get", _mock_cache_get)
    monkeypatch.setattr(cache, "get_many", _mock_cache_get_many)


@pytest.fixture()
def mock_get_metrics_cache(monkeypatch):
    def _mock_cache_get(key, *args, **kwargs):
        return {}

    def _mock_cache_get_many(keys, *args, **kwargs):
        return {}

    monkeypatch.setattr(cache, "get", _mock_cache_get)
    monkeypatch.setattr(cache, "get_many", _mock_cache_get_many)


@pytest.fixture
def make_metrics_cache_params(monkeypatch):
    def _make_cache_params(integration_id, organization_id, team_name=None, team_id=None):
        team_name = team_name or "No team"
        team_id = team_id or "no_team"
        metric_alert_groups_total_key = get_metric_alert_groups_total_key(organization_id)
        metric_alert_groups_response_time_key = get_metric_alert_groups_response_time_key(organization_id)

        def cache_get(key, *args, **kwargs):
            metrics_data = {
                metric_alert_groups_response_time_key: {
                    integration_id: {
                        "integration_name": METRICS_TEST_INTEGRATION_NAME,
                        "team_name": team_name,
                        "team_id": team_id,
                        "org_id": METRICS_TEST_ORG_ID,
                        "slug": METRICS_TEST_INSTANCE_SLUG,
                        "id": METRICS_TEST_INSTANCE_ID,
                        "response_time": [],
                    }
                },
                metric_alert_groups_total_key: {
                    integration_id: {
                        "integration_name": METRICS_TEST_INTEGRATION_NAME,
                        "team_name": team_name,
                        "team_id": team_id,
                        "org_id": METRICS_TEST_ORG_ID,
                        "slug": METRICS_TEST_INSTANCE_SLUG,
                        "id": METRICS_TEST_INSTANCE_ID,
                        "firing": 0,
                        "acknowledged": 0,
                        "silenced": 0,
                        "resolved": 0,
                    }
                },
            }
            return metrics_data.get(key, {})

        return cache_get

    return _make_cache_params


@pytest.fixture
def make_user_was_notified_metrics_cache_params(monkeypatch):
    def _make_cache_params(user_id, organization_id):
        metric_user_was_notified_key = get_metric_user_was_notified_of_alert_groups_key(organization_id)

        def cache_get(key, *args, **kwargs):
            metrics_data = {
                metric_user_was_notified_key: {
                    user_id: {
                        "org_id": METRICS_TEST_ORG_ID,
                        "slug": METRICS_TEST_INSTANCE_SLUG,
                        "id": METRICS_TEST_INSTANCE_ID,
                        "user_username": METRICS_TEST_USER_USERNAME,
                        "counter": 1,
                    }
                },
            }
            return metrics_data.get(key, {})

        return cache_get

    return _make_cache_params
