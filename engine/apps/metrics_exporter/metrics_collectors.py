import re
import typing

from django.core.cache import cache
from prometheus_client import CollectorRegistry
from prometheus_client.metrics_core import CounterMetricFamily, GaugeMetricFamily, HistogramMetricFamily

from apps.alerts.constants import AlertGroupState
from apps.metrics_exporter.constants import (
    ALERT_GROUPS_RESPONSE_TIME,
    ALERT_GROUPS_TOTAL,
    USER_WAS_NOTIFIED_OF_ALERT_GROUPS,
    AlertGroupsResponseTimeMetricsDict,
    AlertGroupsTotalMetricsDict,
    RecalculateOrgMetricsDict,
    UserWasNotifiedOfAlertGroupsMetricsDict,
)
from apps.metrics_exporter.helpers import (
    get_metric_alert_groups_response_time_key,
    get_metric_alert_groups_total_key,
    get_metric_calculation_started_key,
    get_metric_user_was_notified_of_alert_groups_key,
    get_metrics_cache_timer_key,
    get_organization_ids,
)
from apps.metrics_exporter.tasks import start_calculate_and_cache_metrics, start_recalculation_for_new_metric

application_metrics_registry = CollectorRegistry()


RE_ALERT_GROUPS_TOTAL = re.compile(r"{}_(\d+)".format(ALERT_GROUPS_TOTAL))
RE_ALERT_GROUPS_RESPONSE_TIME = re.compile(r"{}_(\d+)".format(ALERT_GROUPS_RESPONSE_TIME))
RE_USER_WAS_NOTIFIED_OF_ALERT_GROUPS = re.compile(r"{}_(\d+)".format(USER_WAS_NOTIFIED_OF_ALERT_GROUPS))


# https://github.com/prometheus/client_python#custom-collectors
class ApplicationMetricsCollector:
    def __init__(self):
        self._buckets = (60, 300, 600, 3600, "+Inf")
        self._stack_labels = [
            "org_id",
            "slug",
            "id",
        ]
        self._integration_labels = [
            "integration",
            "team",
        ] + self._stack_labels
        self._integration_labels_with_state = self._integration_labels + ["state"]
        self._user_labels = ["username"] + self._stack_labels

    def collect(self):
        org_ids = set(get_organization_ids())

        # alert groups total metric: gauge
        alert_groups_total, missing_org_ids_1 = self._get_alert_groups_total_metric(org_ids)
        # alert groups response time metrics: histogram
        alert_groups_response_time_seconds, missing_org_ids_2 = self._get_response_time_metric(org_ids)
        # user was notified of alert groups metrics: counter
        user_was_notified, missing_org_ids_3 = self._get_user_was_notified_of_alert_groups_metric(org_ids)

        # update new metric gradually
        missing_org_ids_3 = self._update_new_metric(USER_WAS_NOTIFIED_OF_ALERT_GROUPS, org_ids, missing_org_ids_3)

        # check for orgs missing any of the metrics or needing a refresh, start recalculation task for missing org ids
        missing_org_ids = missing_org_ids_1 | missing_org_ids_2 | missing_org_ids_3
        self.recalculate_cache_for_missing_org_ids(org_ids, missing_org_ids)

        yield alert_groups_total
        yield alert_groups_response_time_seconds
        yield user_was_notified

    def _get_alert_groups_total_metric(self, org_ids):
        alert_groups_total = GaugeMetricFamily(
            ALERT_GROUPS_TOTAL, "All alert groups", labels=self._integration_labels_with_state
        )
        processed_org_ids = set()
        alert_groups_total_keys = [get_metric_alert_groups_total_key(org_id) for org_id in org_ids]
        org_ag_states: typing.Dict[str, typing.Dict[int, AlertGroupsTotalMetricsDict]] = cache.get_many(
            alert_groups_total_keys
        )
        for org_key, ag_states in org_ag_states.items():
            for integration, integration_data in ag_states.items():
                # Labels values should have the same order as _integration_labels_with_state
                labels_values = [
                    integration_data["integration_name"],  # integration
                    integration_data["team_name"],  # team
                    integration_data["org_id"],  # grafana org_id
                    integration_data["slug"],  # grafana instance slug
                    integration_data["id"],  # grafana instance id
                ]
                labels_values = list(map(str, labels_values))
                for state in AlertGroupState:
                    alert_groups_total.add_metric(labels_values + [state.value], integration_data[state.value])
            org_id_from_key = RE_ALERT_GROUPS_TOTAL.match(org_key).groups()[0]
            processed_org_ids.add(int(org_id_from_key))
        missing_org_ids = org_ids - processed_org_ids
        return alert_groups_total, missing_org_ids

    def _get_response_time_metric(self, org_ids):
        alert_groups_response_time_seconds = HistogramMetricFamily(
            ALERT_GROUPS_RESPONSE_TIME,
            "Users response time to alert groups in 7 days (seconds)",
            labels=self._integration_labels,
        )
        processed_org_ids = set()
        alert_groups_response_time_keys = [get_metric_alert_groups_response_time_key(org_id) for org_id in org_ids]
        org_ag_response_times: typing.Dict[str, typing.Dict[int, AlertGroupsResponseTimeMetricsDict]] = cache.get_many(
            alert_groups_response_time_keys
        )
        for org_key, ag_response_time in org_ag_response_times.items():
            for integration, integration_data in ag_response_time.items():
                # Labels values should have the same order as _integration_labels
                labels_values = [
                    integration_data["integration_name"],  # integration
                    integration_data["team_name"],  # team
                    integration_data["org_id"],  # grafana org_id
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
        missing_org_ids = org_ids - processed_org_ids
        return alert_groups_response_time_seconds, missing_org_ids

    def _get_user_was_notified_of_alert_groups_metric(self, org_ids):
        user_was_notified = CounterMetricFamily(
            USER_WAS_NOTIFIED_OF_ALERT_GROUPS, "Number of alert groups user was notified of", labels=self._user_labels
        )
        processed_org_ids = set()
        user_was_notified_keys = [get_metric_user_was_notified_of_alert_groups_key(org_id) for org_id in org_ids]
        org_users: typing.Dict[str, typing.Dict[int, UserWasNotifiedOfAlertGroupsMetricsDict]] = cache.get_many(
            user_was_notified_keys
        )
        for org_key, users in org_users.items():
            for user, user_data in users.items():
                # Labels values should have the same order as _user_labels
                labels_values = [
                    user_data["user_username"],  # username
                    user_data["org_id"],  # grafana org_id
                    user_data["slug"],  # grafana instance slug
                    user_data["id"],  # grafana instance id
                ]
                labels_values = list(map(str, labels_values))
                user_was_notified.add_metric(labels_values, user_data["counter"])
            org_id_from_key = RE_USER_WAS_NOTIFIED_OF_ALERT_GROUPS.match(org_key).groups()[0]
            processed_org_ids.add(int(org_id_from_key))
        missing_org_ids = org_ids - processed_org_ids
        return user_was_notified, missing_org_ids

    def _update_new_metric(self, metric_name, org_ids, missing_org_ids):
        """
        This method is used for new metrics to calculate metrics gradually and avoid force recalculation for all orgs
        """
        calculation_started_key = get_metric_calculation_started_key(metric_name)
        is_calculation_started = cache.get(calculation_started_key)
        if len(missing_org_ids) == len(org_ids) or is_calculation_started:
            missing_org_ids = set()
            if not is_calculation_started:
                start_recalculation_for_new_metric.apply_async((metric_name,))
        return missing_org_ids

    def recalculate_cache_for_missing_org_ids(self, org_ids, missing_org_ids):
        cache_timer_for_org_keys = [get_metrics_cache_timer_key(org_id) for org_id in org_ids]
        cache_timers_for_org = cache.get_many(cache_timer_for_org_keys)
        recalculate_orgs: typing.List[RecalculateOrgMetricsDict] = []
        for org_id in org_ids:
            force_task = org_id in missing_org_ids
            if force_task or not cache_timers_for_org.get(get_metrics_cache_timer_key(org_id)):
                recalculate_orgs.append({"organization_id": org_id, "force": force_task})
        if recalculate_orgs:
            start_calculate_and_cache_metrics.apply_async((recalculate_orgs,))

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
