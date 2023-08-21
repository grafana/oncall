from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.test import override_settings

from apps.alerts.tasks import notify_user_task
from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord
from apps.metrics_exporter.helpers import (
    get_metric_alert_groups_response_time_key,
    get_metric_alert_groups_total_key,
    get_metric_user_was_notified_of_alert_groups_key,
    metrics_bulk_update_team_label_cache,
)
from apps.metrics_exporter.metrics_cache_manager import MetricsCacheManager
from apps.metrics_exporter.tests.conftest import (
    METRICS_TEST_INSTANCE_ID,
    METRICS_TEST_INSTANCE_SLUG,
    METRICS_TEST_INTEGRATION_NAME,
    METRICS_TEST_ORG_ID,
    METRICS_TEST_USER_USERNAME,
)


@patch("apps.alerts.models.alert_group_log_record.tasks.send_update_log_report_signal.apply_async")
@patch("apps.alerts.models.alert_group.alert_group_action_triggered_signal.send")
@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
def test_update_metric_alert_groups_total_cache_on_action(
    mocked_send_log_signal,
    mocked_action_signal_send,
    make_organization,
    make_user_for_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_metrics_cache_params,
    monkeypatch,
):
    organization = make_organization(
        org_id=METRICS_TEST_ORG_ID,
        stack_slug=METRICS_TEST_INSTANCE_SLUG,
        stack_id=METRICS_TEST_INSTANCE_ID,
    )
    user = make_user_for_organization(organization)
    alert_receive_channel = make_alert_receive_channel(organization, verbal_name=METRICS_TEST_INTEGRATION_NAME)

    metric_alert_groups_total_key = get_metric_alert_groups_total_key(organization.id)

    expected_result_metric_alert_groups_total = {
        alert_receive_channel.id: {
            "integration_name": alert_receive_channel.verbal_name,
            "team_name": "No team",
            "team_id": "no_team",
            "org_id": organization.org_id,
            "slug": organization.stack_slug,
            "id": organization.stack_id,
            "firing": 0,
            "silenced": 0,
            "acknowledged": 0,
            "resolved": 0,
        }
    }

    expected_result_firing = {
        "firing": 1,
        "silenced": 0,
        "acknowledged": 0,
        "resolved": 0,
    }

    expected_result_acked = {
        "firing": 0,
        "silenced": 0,
        "acknowledged": 1,
        "resolved": 0,
    }

    expected_result_resolved = {
        "firing": 0,
        "silenced": 0,
        "acknowledged": 0,
        "resolved": 1,
    }

    expected_result_silenced = {
        "firing": 0,
        "silenced": 1,
        "acknowledged": 0,
        "resolved": 0,
    }

    metrics_cache = make_metrics_cache_params(alert_receive_channel.id, organization.id)
    monkeypatch.setattr(cache, "get", metrics_cache)

    def get_called_arg_index_and_compare_results(update_expected_result):
        """find index for the metric argument, that was set in cache"""
        for idx, called_arg in enumerate(mock_cache_set_called_args):
            if idx >= arg_idx and called_arg.args[0] == metric_alert_groups_total_key:
                expected_result_metric_alert_groups_total[alert_receive_channel.id].update(update_expected_result)
                assert called_arg.args[1] == expected_result_metric_alert_groups_total
                return idx + 1
        raise AssertionError

    with patch("apps.metrics_exporter.tasks.cache.set") as mock_cache_set:
        arg_idx = 0
        alert_group = make_alert_group(alert_receive_channel)
        make_alert(alert_group=alert_group, raw_request_data={})

        # check alert_groups_total metric cache, get called args
        mock_cache_set_called_args = mock_cache_set.call_args_list
        arg_idx = get_called_arg_index_and_compare_results(expected_result_firing)

        alert_group.acknowledge_by_user(user)
        arg_idx = get_called_arg_index_and_compare_results(expected_result_acked)

        alert_group.un_acknowledge_by_user(user)
        arg_idx = get_called_arg_index_and_compare_results(expected_result_firing)

        alert_group.resolve_by_user(user)
        arg_idx = get_called_arg_index_and_compare_results(expected_result_resolved)

        alert_group.un_resolve_by_user(user)
        arg_idx = get_called_arg_index_and_compare_results(expected_result_firing)

        alert_group.silence_by_user(user, silence_delay=None)
        arg_idx = get_called_arg_index_and_compare_results(expected_result_silenced)

        alert_group.un_silence_by_user(user)
        get_called_arg_index_and_compare_results(expected_result_firing)


@patch("apps.alerts.models.alert_group_log_record.tasks.send_update_log_report_signal.apply_async")
@patch("apps.alerts.models.alert_group.alert_group_action_triggered_signal.send")
@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
def test_update_metric_alert_groups_response_time_cache_on_action(
    mocked_send_log_signal,
    mocked_action_signal_send,
    make_organization,
    make_user_for_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    monkeypatch,
    make_metrics_cache_params,
):
    organization = make_organization(
        org_id=METRICS_TEST_ORG_ID,
        stack_slug=METRICS_TEST_INSTANCE_SLUG,
        stack_id=METRICS_TEST_INSTANCE_ID,
    )
    user = make_user_for_organization(organization)
    alert_receive_channel = make_alert_receive_channel(organization, verbal_name=METRICS_TEST_INTEGRATION_NAME)

    metric_alert_groups_response_time_key = get_metric_alert_groups_response_time_key(organization.id)

    expected_result_metric_alert_groups_response_time = {
        alert_receive_channel.id: {
            "integration_name": alert_receive_channel.verbal_name,
            "team_name": "No team",
            "team_id": "no_team",
            "org_id": organization.org_id,
            "slug": organization.stack_slug,
            "id": organization.stack_id,
            "response_time": [],
        }
    }

    metrics_cache = make_metrics_cache_params(alert_receive_channel.id, organization.id)
    monkeypatch.setattr(cache, "get", metrics_cache)

    def get_called_arg_index_and_compare_results():
        """find index for related to the metric argument, that was set in cache"""
        for idx, called_arg in enumerate(mock_cache_set_called_args):
            if idx >= arg_idx and called_arg.args[0] == metric_alert_groups_response_time_key:
                response_time_values = called_arg.args[1][alert_receive_channel.id]["response_time"]
                expected_result_metric_alert_groups_response_time[alert_receive_channel.id].update(
                    {"response_time": response_time_values}
                )
                # response time values len always will be 1 here since cache is mocked and refreshed on every call
                assert len(response_time_values) == 1
                assert called_arg.args[1] == expected_result_metric_alert_groups_response_time
                return idx + 1
        raise AssertionError

    def assert_cache_was_not_changed_by_response_time_metric():
        for idx, called_arg in enumerate(mock_cache_set_called_args):
            if idx >= arg_idx and called_arg.args[0] == metric_alert_groups_response_time_key:
                raise AssertionError

    with patch("apps.metrics_exporter.tasks.cache.set") as mock_cache_set:
        arg_idx = 0
        alert_group_1, alert_group_2, alert_group_3 = [make_alert_group(alert_receive_channel) for _ in range(3)]
        for alert_group in [alert_group_1, alert_group_2, alert_group_3]:
            make_alert(alert_group=alert_group, raw_request_data={})

        # check alert_groups_response_time metric cache, get called args
        mock_cache_set_called_args = mock_cache_set.call_args_list
        # alert_groups_response_time cache shouldn't be updated on create alert group
        assert_cache_was_not_changed_by_response_time_metric()

        alert_group_1.acknowledge_by_user(user)
        arg_idx = get_called_arg_index_and_compare_results()

        # assert that only the first action counts
        alert_group_1.un_acknowledge_by_user(user)
        assert_cache_was_not_changed_by_response_time_metric()

        alert_group_1.resolve_by_user(user)
        assert_cache_was_not_changed_by_response_time_metric()

        alert_group_1.un_resolve_by_user(user)
        assert_cache_was_not_changed_by_response_time_metric()

        alert_group_1.silence_by_user(user, silence_delay=None)
        assert_cache_was_not_changed_by_response_time_metric()

        alert_group_1.un_silence_by_user(user)
        assert_cache_was_not_changed_by_response_time_metric()

        # check that response_time cache updates on other actions with other alert groups
        alert_group_2.resolve_by_user(user)
        arg_idx = get_called_arg_index_and_compare_results()

        alert_group_3.silence_by_user(user, silence_delay=None)
        get_called_arg_index_and_compare_results()


@pytest.mark.django_db
def test_update_metrics_cache_on_update_integration(
    make_organization,
    make_user_for_organization,
    make_alert_receive_channel_with_post_save_signal,
    make_team,
    make_metrics_cache_params,
    monkeypatch,
    mock_get_metrics_cache,
):
    organization = make_organization(
        org_id=METRICS_TEST_ORG_ID,
        stack_slug=METRICS_TEST_INSTANCE_SLUG,
        stack_id=METRICS_TEST_INSTANCE_ID,
    )
    team = make_team(organization)

    metric_alert_groups_total_key = get_metric_alert_groups_total_key(organization.id)
    metric_alert_groups_response_time_key = get_metric_alert_groups_response_time_key(organization.id)

    expected_result_updated_team = {
        "team_name": team.name,
        "team_id": team.id,
    }

    expected_result_updated_name = {"integration_name": "Renamed test integration"}

    def get_called_arg_index_and_compare_results():
        """find index for related to the metric argument, that was set in cache"""
        is_set_metric_alert_groups_total_cache = False
        is_set_metric_alert_groups_response_time_cache = False
        for idx, called_arg in enumerate(mock_cache_set_called_args):
            if idx >= arg_idx and called_arg.args[0] == metric_alert_groups_total_key:
                assert called_arg.args[1] == expected_result_metric_alert_groups_total
                is_set_metric_alert_groups_total_cache = True
            elif idx >= arg_idx and called_arg.args[0] == metric_alert_groups_response_time_key:
                assert called_arg.args[1] == expected_result_metric_alert_groups_response_time
                is_set_metric_alert_groups_response_time_cache = True
            if is_set_metric_alert_groups_total_cache and is_set_metric_alert_groups_response_time_cache:
                return idx + 1
        raise AssertionError

    with patch("apps.metrics_exporter.tasks.cache.set") as mock_cache_set:
        arg_idx = 0
        # check cache update on create integration
        alert_receive_channel = make_alert_receive_channel_with_post_save_signal(
            organization, verbal_name=METRICS_TEST_INTEGRATION_NAME
        )

        expected_result_metric_alert_groups_total = {
            alert_receive_channel.id: {
                "integration_name": METRICS_TEST_INTEGRATION_NAME,
                "team_name": "No team",
                "team_id": "no_team",
                "org_id": organization.org_id,
                "slug": organization.stack_slug,
                "id": organization.stack_id,
                "firing": 0,
                "silenced": 0,
                "acknowledged": 0,
                "resolved": 0,
            }
        }
        expected_result_metric_alert_groups_response_time = {
            alert_receive_channel.id: {
                "integration_name": METRICS_TEST_INTEGRATION_NAME,
                "team_name": "No team",
                "team_id": "no_team",
                "org_id": organization.org_id,
                "slug": organization.stack_slug,
                "id": organization.stack_id,
                "response_time": [],
            }
        }

        mock_cache_set_called_args = mock_cache_set.call_args_list
        arg_idx = get_called_arg_index_and_compare_results()

        metrics_cache = make_metrics_cache_params(alert_receive_channel.id, organization.id)
        monkeypatch.setattr(cache, "get", metrics_cache)

        # check cache update on update integration's team
        alert_receive_channel.team = team
        # clear cached_property
        del alert_receive_channel.team_name
        del alert_receive_channel.team_id_or_no_team

        alert_receive_channel.save()
        for expected_result in [
            expected_result_metric_alert_groups_total,
            expected_result_metric_alert_groups_response_time,
        ]:
            expected_result[alert_receive_channel.id].update(expected_result_updated_team)
        arg_idx = get_called_arg_index_and_compare_results()

        # check cache update on update integration's name
        alert_receive_channel.refresh_from_db()
        alert_receive_channel.verbal_name = expected_result_updated_name["integration_name"]
        # clear cached_property
        del alert_receive_channel.emojized_verbal_name
        alert_receive_channel.save()

        for expected_result in [
            expected_result_metric_alert_groups_total,
            expected_result_metric_alert_groups_response_time,
        ]:
            expected_result[alert_receive_channel.id].update(expected_result_updated_name)
        arg_idx = get_called_arg_index_and_compare_results()

        # check cache update on update integration's name
        alert_receive_channel.refresh_from_db()
        alert_receive_channel.verbal_name = expected_result_updated_name["integration_name"]
        # clear cached_property
        del alert_receive_channel.emojized_verbal_name
        alert_receive_channel.save()

        for expected_result in [
            expected_result_metric_alert_groups_total,
            expected_result_metric_alert_groups_response_time,
        ]:
            expected_result[alert_receive_channel.id].update(expected_result_updated_name)
        arg_idx = get_called_arg_index_and_compare_results()

        # check cache update on delete integration
        alert_receive_channel.refresh_from_db()
        alert_receive_channel.delete()

        for expected_result in [
            expected_result_metric_alert_groups_total,
            expected_result_metric_alert_groups_response_time,
        ]:
            expected_result.pop(alert_receive_channel.id)
        get_called_arg_index_and_compare_results()


@pytest.mark.django_db
def test_update_metrics_cache_on_update_team(
    make_organization,
    make_user_for_organization,
    make_alert_receive_channel,
    make_team,
    make_metrics_cache_params,
    monkeypatch,
    mock_get_metrics_cache,
):
    organization = make_organization(
        org_id=METRICS_TEST_ORG_ID,
        stack_slug=METRICS_TEST_INSTANCE_SLUG,
        stack_id=METRICS_TEST_INSTANCE_ID,
    )
    team = make_team(organization)
    alert_receive_channel = make_alert_receive_channel(
        organization, verbal_name=METRICS_TEST_INTEGRATION_NAME, team=team
    )
    metrics_cache = make_metrics_cache_params(alert_receive_channel.id, organization.id, team.name, team.id)
    monkeypatch.setattr(cache, "get", metrics_cache)

    metric_alert_groups_total_key = get_metric_alert_groups_total_key(organization.id)
    metric_alert_groups_response_time_key = get_metric_alert_groups_response_time_key(organization.id)

    new_team_name = "Test team renamed"

    expected_result_metric_alert_groups_total = {
        alert_receive_channel.id: {
            "integration_name": METRICS_TEST_INTEGRATION_NAME,
            "team_name": new_team_name,
            "team_id": team.id,
            "org_id": organization.org_id,
            "slug": organization.stack_slug,
            "id": organization.stack_id,
            "firing": 0,
            "silenced": 0,
            "acknowledged": 0,
            "resolved": 0,
        }
    }
    expected_result_metric_alert_groups_response_time = {
        alert_receive_channel.id: {
            "integration_name": METRICS_TEST_INTEGRATION_NAME,
            "team_name": new_team_name,
            "team_id": team.id,
            "org_id": organization.org_id,
            "slug": organization.stack_slug,
            "id": organization.stack_id,
            "response_time": [],
        }
    }

    expected_result_delete_team = {
        "team_name": "No team",
        "team_id": "no_team",
    }

    def get_called_arg_index_and_compare_results():
        """find index for related to the metric argument, that was set in cache"""
        is_set_metric_alert_groups_total_cache = False
        is_set_metric_alert_groups_response_time_cache = False
        for idx, called_arg in enumerate(mock_cache_set_called_args):
            if idx >= arg_idx and called_arg.args[0] == metric_alert_groups_total_key:
                assert called_arg.args[1] == expected_result_metric_alert_groups_total
                is_set_metric_alert_groups_total_cache = True
            elif idx >= arg_idx and called_arg.args[0] == metric_alert_groups_response_time_key:
                assert called_arg.args[1] == expected_result_metric_alert_groups_response_time
                is_set_metric_alert_groups_response_time_cache = True
            if is_set_metric_alert_groups_total_cache and is_set_metric_alert_groups_response_time_cache:
                return idx + 1
        raise AssertionError

    team.name = new_team_name
    team.save()

    with patch("apps.metrics_exporter.tasks.cache.set") as mock_cache_set:
        arg_idx = 0
        mock_cache_set_called_args = mock_cache_set.call_args_list

        metrics_team_to_update = MetricsCacheManager.update_team_diff({}, team.id, new_name=new_team_name)
        metrics_bulk_update_team_label_cache(metrics_team_to_update, organization.id)
        arg_idx = get_called_arg_index_and_compare_results()

        metrics_team_to_update = MetricsCacheManager.update_team_diff({}, team.id, deleted=True)
        metrics_bulk_update_team_label_cache(metrics_team_to_update, organization.id)
        for expected_result in [
            expected_result_metric_alert_groups_total,
            expected_result_metric_alert_groups_response_time,
        ]:
            expected_result[alert_receive_channel.id].update(expected_result_delete_team)
        get_called_arg_index_and_compare_results()


@patch("apps.alerts.tasks.notify_user.perform_notification")
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
@pytest.mark.django_db
def test_update_metrics_cache_on_user_notification(
    mocked_perform_notification_task,
    make_organization,
    make_user_for_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_user_notification_policy,
    make_user_notification_policy_log_record,
    make_user_was_notified_metrics_cache_params,
    monkeypatch,
    mock_get_metrics_cache,
):
    organization = make_organization(
        org_id=METRICS_TEST_ORG_ID,
        stack_slug=METRICS_TEST_INSTANCE_SLUG,
        stack_id=METRICS_TEST_INSTANCE_ID,
    )
    alert_receive_channel = make_alert_receive_channel(
        organization,
        verbal_name=METRICS_TEST_INTEGRATION_NAME,
    )
    user = make_user_for_organization(organization, username=METRICS_TEST_USER_USERNAME)

    notification_policy_1 = make_user_notification_policy(user, step=UserNotificationPolicy.Step.NOTIFY)
    make_user_notification_policy(user, step=UserNotificationPolicy.Step.NOTIFY)

    alert_group_1 = make_alert_group(alert_receive_channel)
    alert_group_2 = make_alert_group(alert_receive_channel)

    make_user_notification_policy_log_record(
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
        author=user,
        alert_group=alert_group_1,
    )

    metrics_cache = make_user_was_notified_metrics_cache_params(user.id, organization.id)
    monkeypatch.setattr(cache, "get", metrics_cache)

    metric_user_was_notified_key = get_metric_user_was_notified_of_alert_groups_key(organization.id)

    expected_result_metric_user_was_notified = {
        user.id: {
            "org_id": organization.org_id,
            "slug": organization.stack_slug,
            "id": organization.stack_id,
            "user_username": METRICS_TEST_USER_USERNAME,
            "counter": 1,
        }
    }

    def get_called_arg_index_and_compare_results(cache_was_updated=False):
        """find index for the metric argument, that was set in cache"""
        for idx, called_arg in enumerate(mock_cache_set_called_args):
            if idx >= arg_idx and called_arg.args[0] == metric_user_was_notified_key:
                assert called_arg.args[1] == expected_result_metric_user_was_notified
                return idx + 1
        if cache_was_updated:
            raise AssertionError
        return arg_idx

    with patch("apps.metrics_exporter.tasks.cache.set") as mock_cache_set:
        arg_idx = 0
        notify_user_task(user.id, alert_group_1.id)

        # check user_was_notified_of_alert_groups metric cache, get called args
        mock_cache_set_called_args = mock_cache_set.call_args_list
        arg_idx = get_called_arg_index_and_compare_results()

        # counter grows after the first notification of alert group
        notify_user_task(user.id, alert_group_2.id)
        expected_result_metric_user_was_notified[user.id]["counter"] += 1
        arg_idx = get_called_arg_index_and_compare_results(cache_was_updated=True)

        # counter doesn't grow after the second notification of alert group
        notify_user_task(user.id, alert_group_2.id, previous_notification_policy_pk=notification_policy_1.id)
        arg_idx = get_called_arg_index_and_compare_results()
