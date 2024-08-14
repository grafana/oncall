from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.test import override_settings
from prometheus_client import CollectorRegistry, generate_latest

from apps.alerts.constants import AlertGroupState
from apps.metrics_exporter.constants import (
    ALERT_GROUPS_RESPONSE_TIME,
    ALERT_GROUPS_TOTAL,
    NO_SERVICE_VALUE,
    USER_WAS_NOTIFIED_OF_ALERT_GROUPS,
)
from apps.metrics_exporter.helpers import get_metric_alert_groups_response_time_key, get_metric_alert_groups_total_key
from apps.metrics_exporter.metrics_collectors import ApplicationMetricsCollector
from apps.metrics_exporter.tests.conftest import METRICS_TEST_SERVICE_NAME
from settings.base import (
    METRIC_ALERT_GROUPS_RESPONSE_TIME_NAME,
    METRIC_ALERT_GROUPS_TOTAL_NAME,
    METRIC_USER_WAS_NOTIFIED_OF_ALERT_GROUPS_NAME,
)


# redis cluster usage modifies the cache keys for some operations, so we need to test both cases
# see common.cache.ensure_cache_key_allocates_to_the_same_hash_slot for more details
@pytest.mark.parametrize("use_redis_cluster", [True, False])
@pytest.mark.parametrize(
    "metric_base_names_and_metric_names",
    [
        [
            [METRIC_ALERT_GROUPS_TOTAL_NAME, METRIC_USER_WAS_NOTIFIED_OF_ALERT_GROUPS_NAME],
            [ALERT_GROUPS_TOTAL, USER_WAS_NOTIFIED_OF_ALERT_GROUPS],
        ],
        [[METRIC_ALERT_GROUPS_RESPONSE_TIME_NAME], [ALERT_GROUPS_RESPONSE_TIME]],
        [
            [
                METRIC_ALERT_GROUPS_TOTAL_NAME,
                METRIC_ALERT_GROUPS_RESPONSE_TIME_NAME,
                METRIC_USER_WAS_NOTIFIED_OF_ALERT_GROUPS_NAME,
            ],
            [ALERT_GROUPS_TOTAL, USER_WAS_NOTIFIED_OF_ALERT_GROUPS, ALERT_GROUPS_RESPONSE_TIME],
        ],
    ],
)
@patch("apps.metrics_exporter.metrics_collectors.get_organization_ids", return_value=[1])
@patch("apps.metrics_exporter.metrics_collectors.start_calculate_and_cache_metrics.apply_async")
@pytest.mark.django_db
def test_application_metrics_collectors(
    mocked_org_ids,
    mocked_start_calculate_and_cache_metrics,
    mock_cache_get_metrics_for_collector,
    use_redis_cluster,
    metric_base_names_and_metric_names,
    settings,
):
    """Test that ApplicationMetricsCollector generates expected metrics from cache"""

    def get_expected_labels(service_name=NO_SERVICE_VALUE, **kwargs):
        labels = {
            "integration": "Test metrics integration",
            "team": "Test team",
            "org_id": "1",
            "slug": "Test stack",
            "id": "1",
            "service_name": service_name,
        }
        labels.update(kwargs)
        return labels

    with override_settings(USE_REDIS_CLUSTER=use_redis_cluster):
        settings.METRICS_TO_COLLECT = metric_base_names_and_metric_names[0]
        collector = ApplicationMetricsCollector()
        test_metrics_registry = CollectorRegistry()
        test_metrics_registry.register(collector)

        metrics = [i for i in test_metrics_registry.collect()]
        assert len(metrics) == len(metric_base_names_and_metric_names[1])

        for metric in metrics:
            assert metric.name in metric_base_names_and_metric_names[1]
            if metric.name == ALERT_GROUPS_TOTAL:
                # 2 integrations with labels for each alert group state per service
                assert len(metric.samples) == len(AlertGroupState) * 3  # 2 from 1st integration and 1 from 2nd
                assert {0, 2, 3, 4, 5, 12, 13, 14, 15} == set(sample.value for sample in metric.samples)
                # check that labels were set correctly
                expected_labels_no_service = get_expected_labels(state="firing")
                expected_labels_test_service = get_expected_labels(METRICS_TEST_SERVICE_NAME, state="firing")
                metric_labels = [sample.labels for sample in metric.samples]
                for expected_labels in [expected_labels_no_service, expected_labels_test_service]:
                    assert expected_labels in metric_labels
            elif metric.name == ALERT_GROUPS_RESPONSE_TIME:
                # integration with labels for each of 2 service_name values in collector's bucket + _count and _sum
                # histogram values
                # ignore integration without response_time data
                assert len(metric.samples) == (len(collector._buckets) + 2) * 2  # 2 from 1st integration, ignore 2nd
                # check that `_sum` values for both services are presented
                assert {36, 862}.issubset(set(sample.value for sample in metric.samples))
                # check that labels were set correctly
                expected_labels_no_service = get_expected_labels()
                expected_labels_test_service = get_expected_labels(METRICS_TEST_SERVICE_NAME)
                metric_labels = [sample.labels for sample in metric.samples]
                for expected_labels in [expected_labels_no_service, expected_labels_test_service]:
                    assert expected_labels in metric_labels
            elif metric.name == USER_WAS_NOTIFIED_OF_ALERT_GROUPS:
                # metric with labels for each notified user
                assert len(metric.samples) == 1
            else:
                raise AssertionError
        result = generate_latest(test_metrics_registry).decode("utf-8")
        assert result is not None
        assert mocked_org_ids.called
        # Since there is no recalculation timer for test org in cache, start_calculate_and_cache_metrics must be called
        assert mocked_start_calculate_and_cache_metrics.called
        test_metrics_registry.unregister(collector)


@patch("apps.metrics_exporter.metrics_collectors.get_organization_ids", return_value=[1])
@patch("apps.metrics_exporter.metrics_collectors.start_calculate_and_cache_metrics.apply_async")
@pytest.mark.django_db
def test_application_metrics_collector_with_old_metrics_without_services(
    mocked_org_ids, mocked_start_calculate_and_cache_metrics, mock_cache_get_old_metrics_for_collector
):
    """Test that ApplicationMetricsCollector generates expected metrics from cache"""

    org_id = 1
    collector = ApplicationMetricsCollector()
    test_metrics_registry = CollectorRegistry()
    test_metrics_registry.register(collector)
    metrics = [i for i in test_metrics_registry.collect()]
    assert len(metrics) == 3
    for metric in metrics:
        if metric.name == ALERT_GROUPS_TOTAL:
            alert_groups_total_metrics_cache = cache.get(get_metric_alert_groups_total_key(org_id))
            assert alert_groups_total_metrics_cache and "services" not in alert_groups_total_metrics_cache[1]
            assert len(metric.samples) == 0
        elif metric.name == ALERT_GROUPS_RESPONSE_TIME:
            alert_groups_response_time_metrics_cache = cache.get(get_metric_alert_groups_response_time_key(org_id))
            assert (
                alert_groups_response_time_metrics_cache
                and "services" not in alert_groups_response_time_metrics_cache[1]
            )
            assert len(metric.samples) == 0
        elif metric.name == USER_WAS_NOTIFIED_OF_ALERT_GROUPS:
            # metric with labels for each notified user
            assert len(metric.samples) == 1
        else:
            raise AssertionError
    result = generate_latest(test_metrics_registry).decode("utf-8")
    assert result is not None
    assert mocked_org_ids.called
    # Since there is no recalculation timer for test org in cache, start_calculate_and_cache_metrics must be called
    assert mocked_start_calculate_and_cache_metrics.called
    test_metrics_registry.unregister(collector)
