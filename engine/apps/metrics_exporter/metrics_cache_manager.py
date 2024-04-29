import typing

from apps.alerts.constants import AlertGroupState
from apps.metrics_exporter.helpers import (
    get_response_time_period,
    metrics_update_alert_groups_response_time_cache,
    metrics_update_alert_groups_state_cache,
)


class MetricsCacheManager:
    class _TeamsDiff(typing.TypedDict):
        team_name: str | None
        deleted: bool

    TeamsDiffMap = typing.Dict[int, _TeamsDiff]

    @staticmethod
    def get_default_teams_diff_dict() -> _TeamsDiff:
        return {
            "team_name": None,
            "deleted": False,
        }

    @staticmethod
    def update_team_diff(
        teams_diff: TeamsDiffMap, team_id: int, new_name: str | None = None, deleted: bool = False
    ) -> TeamsDiffMap:
        teams_diff.setdefault(team_id, MetricsCacheManager.get_default_teams_diff_dict())
        teams_diff[team_id]["team_name"] = new_name
        teams_diff[team_id]["deleted"] = deleted
        return teams_diff

    @staticmethod
    def get_default_states_diff_dict():
        default_dict = {
            "previous_states": {state.value: 0 for state in AlertGroupState},
            "new_states": {state.value: 0 for state in AlertGroupState},
        }
        return default_dict

    @staticmethod
    def update_integration_states_diff(metrics_dict, integration_id, service_name, previous_state=None, new_state=None):
        state_per_service = metrics_dict.setdefault(
            integration_id, {service_name: MetricsCacheManager.get_default_states_diff_dict()}
        )
        if previous_state:
            state_value = previous_state
            state_per_service[service_name]["previous_states"][state_value] += 1
        if new_state:
            state_value = new_state
            state_per_service[service_name]["new_states"][state_value] += 1
        return metrics_dict

    @staticmethod
    def metrics_update_state_cache_for_alert_group(
        integration_id, organization_id, service_name, old_state=None, new_state=None
    ):
        """
        Update state metric cache for one alert group.
        """
        metrics_state_diff = MetricsCacheManager.update_integration_states_diff(
            {}, integration_id, service_name, previous_state=old_state, new_state=new_state
        )
        metrics_update_alert_groups_state_cache(metrics_state_diff, organization_id)

    @staticmethod
    def metrics_update_response_time_cache_for_alert_group(
        integration_id, organization_id, response_time_seconds, service_name
    ):
        """
        Update response time metric cache for one alert group.
        """
        metrics_response_time: typing.Dict[int, typing.Dict[str, typing.List[int]]] = {
            integration_id: {service_name: [response_time_seconds]}
        }
        metrics_update_alert_groups_response_time_cache(metrics_response_time, organization_id)

    @staticmethod
    def metrics_update_cache_for_alert_group(
        integration_id,
        organization_id,
        old_state=None,
        new_state=None,
        response_time=None,
        started_at=None,
        service_name=None,
    ):
        """Call methods to update state and response time metrics cache for one alert group."""

        if response_time and old_state == AlertGroupState.FIRING and started_at > get_response_time_period():
            response_time_seconds = int(response_time.total_seconds())
            MetricsCacheManager.metrics_update_response_time_cache_for_alert_group(
                integration_id, organization_id, response_time_seconds, service_name
            )
        if old_state or new_state:
            MetricsCacheManager.metrics_update_state_cache_for_alert_group(
                integration_id, organization_id, service_name, old_state, new_state
            )
