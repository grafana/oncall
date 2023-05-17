from unittest.mock import patch

import pytest

from apps.metrics_exporter.helpers import (
    get_metric_alert_groups_response_time_key,
    get_metric_alert_groups_total_key,
    get_metrics_cache_timer_key,
)
from apps.metrics_exporter.tasks import calculate_and_cache_metrics


@patch("apps.alerts.models.alert_group.MetricsCacheManager.metrics_update_state_cache_for_alert_group")
@pytest.mark.django_db
def test_calculate_and_cache_metrics_task(
    mocked_update_state_cache,
    make_organization,
    make_user_for_organization,
    make_team,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
):
    METRICS_RESPONSE_TIME_LEN = 3  # 1 for each alert group with changed state (acked, resolved, silenced)
    organization = make_organization()
    team = make_team(organization)

    alert_receive_channel_1 = make_alert_receive_channel(organization)
    alert_receive_channel_2 = make_alert_receive_channel(organization, team=team)
    for alert_receive_channel in [alert_receive_channel_1, alert_receive_channel_2]:
        for _ in range(2):
            alert_group = make_alert_group(alert_receive_channel)
            make_alert(alert_group=alert_group, raw_request_data={})

        alert_group_to_ack = make_alert_group(alert_receive_channel)
        make_alert(alert_group=alert_group_to_ack, raw_request_data={})
        alert_group_to_ack.acknowledge()

        alert_group_to_res = make_alert_group(alert_receive_channel)
        make_alert(alert_group=alert_group_to_res, raw_request_data={})
        alert_group_to_res.resolve()

        alert_group_to_sil = make_alert_group(alert_receive_channel)
        make_alert(alert_group=alert_group_to_sil, raw_request_data={})
        alert_group_to_sil.silence()

    metrics_cache_timer_key = get_metrics_cache_timer_key(organization.id)
    metric_alert_groups_total_key = get_metric_alert_groups_total_key(organization.id)
    metric_alert_groups_response_time_key = get_metric_alert_groups_response_time_key(organization.id)

    expected_result_metric_alert_groups_total = {
        alert_receive_channel_1.id: {
            "integration_name": alert_receive_channel_1.verbal_name,
            "team_name": "No team",
            "team_id": "no_team",
            "org_id": organization.org_id,
            "slug": organization.stack_slug,
            "id": organization.stack_id,
            "firing": 2,
            "silenced": 1,
            "acknowledged": 1,
            "resolved": 1,
        },
        alert_receive_channel_2.id: {
            "integration_name": alert_receive_channel_2.verbal_name,
            "team_name": team.name,
            "team_id": team.id,
            "org_id": organization.org_id,
            "slug": organization.stack_slug,
            "id": organization.stack_id,
            "firing": 2,
            "silenced": 1,
            "acknowledged": 1,
            "resolved": 1,
        },
    }
    expected_result_metric_alert_groups_response_time = {
        alert_receive_channel_1.id: {
            "integration_name": alert_receive_channel_1.verbal_name,
            "team_name": "No team",
            "team_id": "no_team",
            "org_id": organization.org_id,
            "slug": organization.stack_slug,
            "id": organization.stack_id,
            "response_time": [],
        },
        alert_receive_channel_2.id: {
            "integration_name": alert_receive_channel_2.verbal_name,
            "team_name": team.name,
            "team_id": team.id,
            "org_id": organization.org_id,
            "slug": organization.stack_slug,
            "id": organization.stack_id,
            "response_time": [],
        },
    }

    with patch("apps.metrics_exporter.tasks.cache.set") as mock_cache_set:
        calculate_and_cache_metrics(organization.id)
        args = mock_cache_set.call_args_list
        assert args[0].args[0] == metrics_cache_timer_key

        # check alert_groups_total metric cache
        metric_alert_groups_total_values = args[1].args
        assert metric_alert_groups_total_values[0] == metric_alert_groups_total_key
        assert metric_alert_groups_total_values[1] == expected_result_metric_alert_groups_total

        # check alert_groups_response_time metric cache
        metric_alert_groups_response_time_values = args[2].args
        assert metric_alert_groups_response_time_values[0] == metric_alert_groups_response_time_key
        for integration_id, values in metric_alert_groups_response_time_values[1].items():
            assert len(values["response_time"]) == METRICS_RESPONSE_TIME_LEN
            # set response time to expected result because it is calculated on fly
            expected_result_metric_alert_groups_response_time[integration_id]["response_time"] = values["response_time"]
        assert metric_alert_groups_response_time_values[1] == expected_result_metric_alert_groups_response_time
