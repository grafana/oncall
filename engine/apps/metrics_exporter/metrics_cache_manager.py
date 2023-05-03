from apps.alerts.constants import ALERTGROUP_STATES, STATE_FIRING
from apps.metrics_exporter.helpers import get_response_time_period
from apps.metrics_exporter.tasks import (
    metrics_update_alert_groups_response_time_cache,
    metrics_update_alert_groups_state_cache,
)


class MetricsCacheManager:
    @staticmethod
    def get_default_teams_diff_dict():
        default_dict = {
            "team_name": None,
            "deleted": False,
        }
        return default_dict

    @staticmethod
    def update_team_diff(teams_diff, team_id, new_name=None, deleted=False):
        teams_diff.setdefault(team_id, MetricsCacheManager.get_default_teams_diff_dict())
        teams_diff[team_id]["team_name"] = new_name
        teams_diff[team_id]["deleted"] = deleted
        return teams_diff

    @staticmethod
    def get_default_states_diff_dict():
        default_dict = {
            "previous_states": {state: 0 for state in ALERTGROUP_STATES},
            "new_states": {state: 0 for state in ALERTGROUP_STATES},
        }
        return default_dict

    @staticmethod
    def update_integration_states_diff(metrics_dict, integration_id, previous_state=None, new_state=None):
        metrics_dict.setdefault(integration_id, MetricsCacheManager.get_default_states_diff_dict())
        if previous_state:
            metrics_dict[integration_id]["previous_states"][previous_state] += 1
        if new_state:
            metrics_dict[integration_id]["new_states"][new_state] += 1
        return metrics_dict

    @staticmethod
    def update_integration_response_time_diff(metrics_dict, integration_id, response_time_seconds):
        metrics_dict.setdefault(integration_id, [])
        metrics_dict[integration_id].append(response_time_seconds)
        return metrics_dict

    @staticmethod
    def metrics_update_state_cache_for_alert_group(
        integration_id, organization_id=None, old_state=None, new_state=None
    ):
        # todo:metrics: add comment
        metrics_state_diff = MetricsCacheManager.update_integration_states_diff(
            {}, integration_id, previous_state=old_state, new_state=new_state
        )
        if organization_id:
            metrics_update_alert_groups_state_cache(metrics_state_diff, organization_id)
        else:
            metrics_update_alert_groups_state_cache.apply_async((metrics_state_diff,))

    @staticmethod
    def metrics_update_response_time_cache_for_alert_group(integration_id, organization_id, response_time_seconds):
        # todo:metrics: add comment
        metrics_response_time = MetricsCacheManager.update_integration_response_time_diff(
            {}, integration_id, response_time_seconds
        )
        if organization_id:
            metrics_update_alert_groups_response_time_cache(metrics_response_time, organization_id)
        else:
            metrics_update_alert_groups_response_time_cache.apply_async((metrics_response_time,))

    @staticmethod
    def metrics_update_cache_for_alert_group(
        integration_id, organization_id=None, old_state=None, new_state=None, response_time=None, started_at=None
    ):
        # todo:metrics: add comment
        if response_time and old_state == STATE_FIRING and started_at > get_response_time_period():
            response_time_seconds = int(response_time.total_seconds())
            MetricsCacheManager.metrics_update_response_time_cache_for_alert_group(
                integration_id, organization_id, response_time_seconds
            )
        if old_state or new_state:
            MetricsCacheManager.metrics_update_state_cache_for_alert_group(
                integration_id, organization_id, old_state, new_state
            )

    @staticmethod
    def metrics_update_diff_for_alert_group(
        integration_id,
        response_time_diff,
        states_diff,
        old_state=None,
        new_state=None,
        response_time=None,
        started_at=None,
    ):
        # todo:metrics: add comment
        if response_time and old_state == STATE_FIRING and started_at > get_response_time_period():
            response_time_seconds = int(response_time.total_seconds())
            response_time_diff = MetricsCacheManager.update_integration_response_time_diff(
                response_time_diff, integration_id, response_time_seconds
            )

        if old_state or new_state:
            states_diff = MetricsCacheManager.update_integration_states_diff(
                states_diff, integration_id, old_state, new_state
            )
        return response_time_diff, states_diff
