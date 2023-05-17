import typing

from django.core.cache import cache
from prometheus_client import CollectorRegistry
from prometheus_client.metrics_core import GaugeMetricFamily, HistogramMetricFamily

from apps.alerts.constants import ALERTGROUP_STATES
from apps.metrics_exporter.constants import (
    ALERT_GROUPS_RESPONSE_TIME,
    ALERT_GROUPS_TOTAL,
    AlertGroupsResponseTimeMetricsDict,
    AlertGroupsTotalMetricsDict,
    RecalculateOrgMetricsDict,
)
from apps.metrics_exporter.helpers import (
    get_metric_alert_groups_response_time_key,
    get_metric_alert_groups_total_key,
    get_metrics_cache_timer_for_organization,
    get_organization_ids,
)
from apps.metrics_exporter.tasks import start_calculate_and_cache_metrics

application_metrics_registry = CollectorRegistry()


# https://github.com/prometheus/client_python#custom-collectors
class ApplicationMetricsCollector:
    def __init__(self):
        self._buckets = (60, 300, 600, 3600, "+Inf")
        self._labels = [
            "integration",
            "team",
            "org_id",
            "slug",
            "id",
        ]
        self._labels_with_state = self._labels + ["state"]

    def collect(self):
        alert_groups_total = GaugeMetricFamily(ALERT_GROUPS_TOTAL, "All alert groups", labels=self._labels_with_state)
        alert_groups_response_time_seconds = HistogramMetricFamily(
            ALERT_GROUPS_RESPONSE_TIME, "Users response time to alert groups in 7 days (seconds)", labels=self._labels
        )

        metrics_to_recalculate = []
        org_ids = get_organization_ids()

        for organization_id in org_ids:
            start_calculation_task = False
            # get alert_groups_total metric
            alert_groups_total_key = get_metric_alert_groups_total_key(organization_id)
            ag_states: typing.Dict[int, AlertGroupsTotalMetricsDict] = cache.get(alert_groups_total_key)

            if ag_states is None:
                start_calculation_task = True
            else:
                for integration, integration_data in ag_states.items():
                    # Labels values should have the same order as _labels
                    labels_values = [
                        integration_data["integration_name"],  # integration
                        integration_data["team_name"],  # team
                        integration_data["org_id"],  # org_id
                        integration_data["slug"],  # grafana instance slug
                        integration_data["id"],  # grafana instance id
                    ]

                    labels_values = list(map(str, labels_values))
                    for state in ALERTGROUP_STATES:
                        alert_groups_total.add_metric(labels_values + [state], integration_data[state])

            # get alert_groups_response_time metric
            alert_groups_response_time_key = get_metric_alert_groups_response_time_key(organization_id)
            ag_response_time: typing.Dict[int, AlertGroupsResponseTimeMetricsDict] = cache.get(
                alert_groups_response_time_key
            )
            if ag_response_time is None:
                start_calculation_task = True
            else:
                for integration, integration_data in ag_response_time.items():
                    # Labels values should have the same order as _labels
                    labels_values = [
                        integration_data["integration_name"],  # integration
                        integration_data["team_name"],  # team
                        integration_data["org_id"],  # org_id
                        integration_data["slug"],  # grafana instance slug
                        integration_data["id"],  # grafana instance id
                    ]
                    labels_values = list(map(str, labels_values))

                    response_time_values = integration_data["response_time"]
                    if not response_time_values:
                        continue
                    buckets, sum_value = self.get_buckets_with_sum(response_time_values)
                    buckets = sorted(list(buckets.items()), key=lambda x: float(x[0]))
                    alert_groups_response_time_seconds.add_metric(labels_values, buckets=buckets, sum_value=sum_value)

            if start_calculation_task or not get_metrics_cache_timer_for_organization(organization_id):
                org_to_recalculate: RecalculateOrgMetricsDict = {
                    "organization_id": organization_id,
                    "force": start_calculation_task,
                }
                metrics_to_recalculate.append(org_to_recalculate)

        if metrics_to_recalculate:
            start_calculate_and_cache_metrics.apply_async((metrics_to_recalculate,))

        yield alert_groups_total
        yield alert_groups_response_time_seconds

    def get_buckets_with_sum(self, values):
        """Put values in correct buckets and count values sum"""
        buckets_values = {str(key): 0 for key in self._buckets}
        sum_value = 0
        for value in values:
            for bucket in self._buckets:
                if value <= float(bucket):
                    buckets_values[str(bucket)] += 1.0
            sum_value += value
        return buckets_values, sum_value


application_metrics_registry.register(ApplicationMetricsCollector())
