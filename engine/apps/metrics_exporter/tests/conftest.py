import pytest
from django.core.cache import cache

from apps.metrics_exporter.constants import (
    ALERT_GROUPS_RESPONSE_TIME,
    ALERT_GROUPS_TOTAL,
    NO_SERVICE_VALUE,
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
METRICS_TEST_SERVICE_NAME = "test_service"


@pytest.fixture()
def mock_cache_get_metrics_for_collector(monkeypatch):
    def _mock_cache_get(key, *args, **kwargs):
        if ALERT_GROUPS_TOTAL in key:
            key = ALERT_GROUPS_TOTAL
        elif ALERT_GROUPS_RESPONSE_TIME in key:
            key = ALERT_GROUPS_RESPONSE_TIME
        elif USER_WAS_NOTIFIED_OF_ALERT_GROUPS in key:
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
                    "services": {
                        NO_SERVICE_VALUE: {
                            "firing": 2,
                            "silenced": 4,
                            "acknowledged": 3,
                            "resolved": 5,
                        },
                        METRICS_TEST_SERVICE_NAME: {
                            "firing": 12,
                            "silenced": 14,
                            "acknowledged": 13,
                            "resolved": 15,
                        },
                    },
                },
                2: {
                    "integration_name": "Empty integration",
                    "team_name": "Test team",
                    "team_id": 1,
                    "org_id": 1,
                    "slug": "Test stack",
                    "id": 2,
                    "services": {
                        NO_SERVICE_VALUE: {
                            "firing": 0,
                            "silenced": 0,
                            "acknowledged": 0,
                            "resolved": 0,
                        },
                    },
                },
            },
            ALERT_GROUPS_RESPONSE_TIME: {
                1: {
                    "integration_name": "Test metrics integration",
                    "team_name": "Test team",
                    "team_id": 1,
                    "org_id": 1,
                    "slug": "Test stack",
                    "id": 1,
                    "services": {NO_SERVICE_VALUE: [2, 10, 200, 650], METRICS_TEST_SERVICE_NAME: [4, 12, 20]},
                },
                2: {
                    "integration_name": "Empty integration",
                    "team_name": "Test team",
                    "team_id": 1,
                    "org_id": 1,
                    "slug": "Test stack",
                    "id": 2,
                    "services": {
                        # if there are no response times available, this integration will be ignored
                        NO_SERVICE_VALUE: [],
                    },
                },
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
                        "services": {
                            NO_SERVICE_VALUE: [],
                        },
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
                        "services": {
                            NO_SERVICE_VALUE: {
                                "firing": 0,
                                "silenced": 0,
                                "acknowledged": 0,
                                "resolved": 0,
                            },
                        },
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
