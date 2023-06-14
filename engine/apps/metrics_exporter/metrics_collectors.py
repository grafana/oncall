import re
import typing

from django.core.cache import cache
from prometheus_client import CollectorRegistry
from prometheus_client.metrics_core import GaugeMetricFamily, HistogramMetricFamily

from apps.alerts.constants import AlertGroupState
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
    get_metrics_cache_timer_key,
    get_organization_ids,
)
from apps.metrics_exporter.tasks import start_calculate_and_cache_metrics

application_metrics_registry = CollectorRegistry()


RE_ALERT_GROUPS_TOTAL = re.compile(r"{}_(\d+)".format(ALERT_GROUPS_TOTAL))
RE_ALERT_GROUPS_RESPONSE_TIME = re.compile(r"{}_(\d+)".format(ALERT_GROUPS_RESPONSE_TIME))


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

        org_ids = set(get_organization_ids())

        # alert groups total metrics
        processed_org_ids = set()
        alert_groups_total_keys = [get_metric_alert_groups_total_key(org_id) for org_id in org_ids]
        org_ag_states: typing.Dict[str, typing.Dict[int, AlertGroupsTotalMetricsDict]] = cache.get_many(
            alert_groups_total_keys
        )
        for org_key, ag_states in org_ag_states.items():
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
                for state in AlertGroupState:
                    alert_groups_total.add_metric(labels_values + [state.value], integration_data[state.value])
            org_id_from_key = RE_ALERT_GROUPS_TOTAL.match(org_key).groups()[0]
            processed_org_ids.add(int(org_id_from_key))
        # get missing orgs
        missing_org_ids_1 = org_ids - processed_org_ids

        # alert groups response time metrics
        processed_org_ids = set()
        alert_groups_response_time_keys = [get_metric_alert_groups_response_time_key(org_id) for org_id in org_ids]
        org_ag_response_times: typing.Dict[str, typing.Dict[int, AlertGroupsResponseTimeMetricsDict]] = cache.get_many(
            alert_groups_response_time_keys
        )
        for org_key, ag_response_time in org_ag_response_times.items():
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
            org_id_from_key = RE_ALERT_GROUPS_RESPONSE_TIME.match(org_key).groups()[0]
            processed_org_ids.add(int(org_id_from_key))
        # get missing orgs
        missing_org_ids_2 = org_ids - processed_org_ids

        # check for orgs missing any of the metrics or needing a refresh
        missing_org_ids = missing_org_ids_1 | missing_org_ids_2
        cache_timer_for_org_keys = [get_metrics_cache_timer_key(org_id) for org_id in org_ids]
        cache_timers_for_org = cache.get_many(cache_timer_for_org_keys)
        recalculate_orgs: typing.List[RecalculateOrgMetricsDict] = []
        for org_id in org_ids:
            force_task = org_id in missing_org_ids
            if force_task or not cache_timers_for_org.get(get_metrics_cache_timer_key(org_id)):
                recalculate_orgs.append({"organization_id": org_id, "force": force_task})
        if recalculate_orgs:
            start_calculate_and_cache_metrics.apply_async((recalculate_orgs,))

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
