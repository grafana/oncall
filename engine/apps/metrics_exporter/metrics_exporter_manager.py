from django.core.cache import cache
from prometheus_client import CollectorRegistry, Gauge, Histogram

from apps.alerts.constants import ALERTGROUP_STATES, STATE_ACKNOWLEDGED, STATE_NEW, STATE_RESOLVED, STATE_SILENCED
from apps.metrics_exporter.constants import ALERT_GROUPS_RESPONSE_TIME, ALERT_GROUPS_TOTAL, METRICS_CACHE_TIMER
from apps.metrics_exporter.helpers import metrics_update_alert_groups_state_cache
from apps.metrics_exporter.tasks import calculate_and_cache_metrics


class MetricsExporterManager:
    @staticmethod
    def collect_metrics_from_cache():
        registry = CollectorRegistry()
        start_calculation_task = False
        ag_states = cache.get(ALERT_GROUPS_TOTAL, {})
        if not ag_states:
            start_calculation_task = True

        alert_groups_states = Gauge(
            name=ALERT_GROUPS_TOTAL,
            documentation="All alert groups",
            labelnames=["integration", "team", "state"],
            registry=registry,
        )
        print(ag_states)  # todo:metrics remove print
        for integration, integration_data in ag_states.items():
            for state in ALERTGROUP_STATES:
                alert_groups_states.labels(
                    integration=integration_data["integration_name"], team=integration_data["team_name"], state=state
                ).set(integration_data[state])

        ag_response_time = cache.get(ALERT_GROUPS_RESPONSE_TIME, {})
        if not ag_response_time:
            start_calculation_task = True

        response_time_seconds = Histogram(
            name=ALERT_GROUPS_RESPONSE_TIME,
            documentation="Users response time to alert groups (seconds)",
            labelnames=["integration", "team"],
            buckets=(60, 300, 600, 3600),
            registry=registry,
        )
        print(ag_response_time)  # todo:metrics remove print

        for integration, integration_data in ag_response_time.items():
            for response_time in integration_data["response_time"]:
                response_time_seconds.labels(
                    integration=integration_data["integration_name"], team=integration_data["team_name"]
                ).observe(int(response_time))

        if start_calculation_task or not cache.get(METRICS_CACHE_TIMER):
            # todo:metrics: check cache timer
            calculate_and_cache_metrics.apply_async(kwargs={"force": start_calculation_task})

        return registry

    @staticmethod
    def get_default_states_diff_dict():
        default_dict = {
            "previous_states": {STATE_RESOLVED: 0, STATE_SILENCED: 0, STATE_NEW: 0, STATE_ACKNOWLEDGED: 0},
            "new_states": {STATE_RESOLVED: 0, STATE_SILENCED: 0, STATE_NEW: 0, STATE_ACKNOWLEDGED: 0},
        }
        return default_dict

    @staticmethod
    def update_integration_response_time(metrics_dict, integration_id, response_time):
        metrics_dict.setdefault(integration_id, [])
        metrics_dict[integration_id].append(response_time)
        return metrics_dict

    @staticmethod
    def update_integration_states_diff(metrics_dict, integration_id, previous_state=None, new_state=None):
        metrics_dict.setdefault(integration_id, MetricsExporterManager.get_default_states_diff_dict())
        if previous_state:
            metrics_dict[integration_id]["previous_states"][previous_state] += 1
        if new_state:
            metrics_dict[integration_id]["new_states"][new_state] += 1
        return metrics_dict

    @staticmethod
    def get_default_teams_diff_dict():
        default_dict = {
            "team_name": None,
            "deleted": False,
        }
        return default_dict

    @staticmethod
    def update_team_diff(teams_diff, team_id, new_name=None, deleted=False):
        teams_diff.setdefault(team_id, MetricsExporterManager.get_default_teams_diff_dict())
        teams_diff[team_id]["team_name"] = new_name
        teams_diff[team_id]["deleted"] = deleted
        return teams_diff

    @staticmethod
    def metrics_update_state_cache_for_alert_group(channel_id, old_state=None, new_state=None):
        # todo:metrics: add comment
        if old_state != new_state:
            metrics_state_diff = MetricsExporterManager.update_integration_states_diff(
                {}, channel_id, previous_state=old_state, new_state=new_state
            )
            metrics_update_alert_groups_state_cache(metrics_state_diff)
