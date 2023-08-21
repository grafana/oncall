from unittest.mock import patch

import pytest
from prometheus_client import CollectorRegistry, generate_latest

from apps.alerts.constants import AlertGroupState
from apps.metrics_exporter.constants import (
    ALERT_GROUPS_RESPONSE_TIME,
    ALERT_GROUPS_TOTAL,
    USER_WAS_NOTIFIED_OF_ALERT_GROUPS,
)
from apps.metrics_exporter.metrics_collectors import ApplicationMetricsCollector


@patch("apps.metrics_exporter.metrics_collectors.get_organization_ids", return_value=[1])
@patch("apps.metrics_exporter.metrics_collectors.start_calculate_and_cache_metrics.apply_async")
@pytest.mark.django_db
def test_application_metrics_collector(
    mocked_org_ids, mocked_start_calculate_and_cache_metrics, mock_cache_get_metrics_for_collector
):
    """Test that ApplicationMetricsCollector generates expected metrics from cache"""
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
