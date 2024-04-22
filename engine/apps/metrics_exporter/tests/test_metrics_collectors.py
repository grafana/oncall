from unittest.mock import patch

import pytest
from django.test import override_settings
from prometheus_client import CollectorRegistry, generate_latest

from apps.alerts.constants import AlertGroupState
from apps.metrics_exporter.constants import (
    ALERT_GROUPS_RESPONSE_TIME,
    ALERT_GROUPS_TOTAL,
    USER_WAS_NOTIFIED_OF_ALERT_GROUPS,
)
from apps.metrics_exporter.metrics_collectors import ApplicationMetricsCollector


# redis cluster usage modifies the cache keys for some operations, so we need to test both cases
# see common.cache.ensure_cache_key_allocates_to_the_same_hash_slot for more details
@pytest.mark.parametrize("use_redis_cluster", [True, False])
@patch("apps.metrics_exporter.metrics_collectors.get_organization_ids", return_value=[1])
@patch("apps.metrics_exporter.metrics_collectors.start_calculate_and_cache_metrics.apply_async")
@pytest.mark.django_db
def test_application_metrics_collector(
    mocked_org_ids, mocked_start_calculate_and_cache_metrics, mock_cache_get_metrics_for_collector, use_redis_cluster
):
    """Test that ApplicationMetricsCollector generates expected metrics from cache"""

    with override_settings(USE_REDIS_CLUSTER=use_redis_cluster):
        collector = ApplicationMetricsCollector()
        test_metrics_registry = CollectorRegistry()
        test_metrics_registry.register(collector)
        for metric in test_metrics_registry.collect():
            if metric.name == ALERT_GROUPS_TOTAL:
                # integration with labels for each alert group state
                assert len(metric.samples) == len(AlertGroupState)
            elif metric.name == ALERT_GROUPS_RESPONSE_TIME:
                # integration with labels for each value in collector's bucket + _count and _sum histogram values
                assert len(metric.samples) == len(collector._buckets) + 2
            elif metric.name == USER_WAS_NOTIFIED_OF_ALERT_GROUPS:
                # metric with labels for each notified user
                assert len(metric.samples) == 1
        result = generate_latest(test_metrics_registry).decode("utf-8")
        assert result is not None
        assert mocked_org_ids.called
        # Since there is no recalculation timer for test org in cache, start_calculate_and_cache_metrics must be called
        assert mocked_start_calculate_and_cache_metrics.called
        test_metrics_registry.unregister(collector)


# todo:metrics: remove later when all cache is updated
@patch("apps.metrics_exporter.metrics_collectors.get_organization_ids", return_value=[1])
@patch("apps.metrics_exporter.metrics_collectors.start_calculate_and_cache_metrics.apply_async")
@pytest.mark.django_db
def test_application_metrics_collector_mixed_cache(
    mocked_org_ids, mocked_start_calculate_and_cache_metrics, mock_cache_get_metrics_for_collector_mixed_versions
):
    """Test that ApplicationMetricsCollector generates expected metrics from previous and new versions of cache"""

    collector = ApplicationMetricsCollector()
    test_metrics_registry = CollectorRegistry()
    test_metrics_registry.register(collector)
    for metric in test_metrics_registry.collect():
        if metric.name == ALERT_GROUPS_TOTAL:
            # integration with labels for each alert group state
            assert len(metric.samples) == len(AlertGroupState) * 2
        elif metric.name == ALERT_GROUPS_RESPONSE_TIME:
            # integration with labels for each value in collector's bucket + _count and _sum histogram values
            assert len(metric.samples) == (len(collector._buckets) + 2) * 2
        elif metric.name == USER_WAS_NOTIFIED_OF_ALERT_GROUPS:
            # metric with labels for each notified user
            assert len(metric.samples) == 1
    result = generate_latest(test_metrics_registry).decode("utf-8")
    assert result is not None
    assert mocked_org_ids.called
    # Since there is no recalculation timer for test org in cache, start_calculate_and_cache_metrics must be called
    assert mocked_start_calculate_and_cache_metrics.called
    test_metrics_registry.unregister(collector)
