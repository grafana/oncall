import hashlib
from unittest.mock import call, patch

import pytest

from apps.alerts.constants import ActionSource, AlertGroupState
from apps.alerts.incident_appearance.renderers.phone_call_renderer import AlertGroupPhoneCallRenderer
from apps.alerts.models import Alert, AlertGroup, AlertGroupLogRecord
from apps.alerts.tasks import wipe
from apps.alerts.tasks.delete_alert_group import (
    delete_alert_group,
    finish_delete_alert_group,
    send_alert_group_signal_for_delete,
)
from apps.slack.client import SlackClient
from apps.slack.errors import SlackAPIMessageNotFoundError, SlackAPIRatelimitError
from apps.slack.models import SlackMessage
from apps.slack.tests.conftest import build_slack_response


@pytest.mark.django_db
def test_render_for_phone_call(
    make_organization_with_slack_team_identity,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
):
    organization, _ = make_organization_with_slack_team_identity()
    alert_receive_channel = make_alert_receive_channel(organization)

    alert_group = make_alert_group(alert_receive_channel)
    SlackMessage.objects.create(channel_id="CWER1ASD", alert_group=alert_group)

    alert_group = make_alert_group(alert_receive_channel)

    make_alert(
        alert_group,
        raw_request_data={
            "status": "firing",
            "labels": {
                "alertname": "TestAlert",
                "region": "eu-1",
            },
            "annotations": {},
            "startsAt": "2018-12-25T15:47:47.377363608Z",
            "endsAt": "0001-01-01T00:00:00Z",
            "generatorURL": "",
        },
    )

    expected_verbose_name = (
        f"to check an Alert Group from Grafana OnCall. "
        f"Alert via {alert_receive_channel.verbal_name} - Grafana Legacy Alerting with title TestAlert triggered 1 times"
    )
    rendered_text = AlertGroupPhoneCallRenderer(alert_group).render()
    assert expected_verbose_name in rendered_text


@pytest.mark.django_db
def test_wipe(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
):
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    alert = make_alert(alert_group, raw_request_data={"test": 42})

    wipe(alert_group.pk, user.pk)

    alert_group.refresh_from_db()
    alert.refresh_from_db()
    assert alert_group.wiped_at is not None
    assert alert_group.wiped_by == user
    assert alert.raw_request_data == {}


@patch.object(SlackClient, "reactions_remove")
@patch.object(SlackClient, "chat_delete")
@pytest.mark.django_db
def test_delete(
    mock_chat_delete,
    mock_reactions_remove,
    make_organization_with_slack_team_identity,
    make_user,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_slack_message,
    make_resolution_note_slack_message,
    django_capture_on_commit_callbacks,
):
    """test alert group deleting"""
    organization, slack_team_identity = make_organization_with_slack_team_identity()
    user = make_user(organization=organization)

    alert_receive_channel = make_alert_receive_channel(organization)

    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group, raw_request_data={})

    # Create Slack messages
    slack_message = make_slack_message(alert_group=alert_group, channel_id="test_channel_id", slack_id="test_slack_id")
    resolution_note_1 = make_resolution_note_slack_message(
        alert_group=alert_group,
        user=user,
        added_by_user=user,
        posted_by_bot=True,
        slack_channel_id="test1_channel_id",
        ts="test1_ts",
    )
    resolution_note_2 = make_resolution_note_slack_message(
        alert_group=alert_group,
        user=user,
        added_by_user=user,
        added_to_resolution_note=True,
        slack_channel_id="test2_channel_id",
        ts="test2_ts",
    )

    assert alert_group.alerts.count() == 1
    assert alert_group.slack_messages.count() == 1
    assert alert_group.resolution_note_slack_messages.count() == 2

    with patch(
        "apps.alerts.tasks.delete_alert_group.send_alert_group_signal_for_delete.delay", return_value=None
    ) as mock_send_alert_group_signal:
        with django_capture_on_commit_callbacks(execute=True):
            delete_alert_group(alert_group.pk, user.pk)
    assert mock_send_alert_group_signal.call_count == 1

    with patch(
        "apps.alerts.tasks.delete_alert_group.finish_delete_alert_group.apply_async", return_value=None
    ) as mock_finish_delete_alert_group:
        send_alert_group_signal_for_delete(*mock_send_alert_group_signal.call_args.args)
    assert mock_finish_delete_alert_group.call_count == 1

    finish_delete_alert_group(alert_group.pk)

    assert not alert_group.alerts.exists()
    assert not alert_group.slack_messages.exists()
    assert not alert_group.resolution_note_slack_messages.exists()

    with pytest.raises(AlertGroup.DoesNotExist):
        alert_group.refresh_from_db()

    # Check that appropriate Slack API calls are made
    assert mock_chat_delete.call_count == 2
    assert mock_chat_delete.call_args_list[0] == call(
        channel=resolution_note_1.slack_channel_id, ts=resolution_note_1.ts
    )
    assert mock_chat_delete.call_args_list[1] == call(channel=slack_message.channel_id, ts=slack_message.slack_id)
    mock_reactions_remove.assert_called_once_with(
        channel=resolution_note_2.slack_channel_id, name="memo", timestamp=resolution_note_2.ts
    )


@pytest.mark.parametrize("api_method", ["reactions_remove", "chat_delete"])
@patch.object(send_alert_group_signal_for_delete, "apply_async")
@pytest.mark.django_db
def test_delete_slack_ratelimit(
    mock_send_alert_group_signal_for_delete,
    api_method,
    make_organization_with_slack_team_identity,
    make_user,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_slack_message,
    make_resolution_note_slack_message,
    django_capture_on_commit_callbacks,
):
    organization, slack_team_identity = make_organization_with_slack_team_identity()
    user = make_user(organization=organization)

    alert_receive_channel = make_alert_receive_channel(organization)

    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group, raw_request_data={})

    # Create Slack messages
    make_slack_message(alert_group=alert_group, channel_id="test_channel_id", slack_id="test_slack_id")
    make_resolution_note_slack_message(
        alert_group=alert_group,
        user=user,
        added_by_user=user,
        posted_by_bot=True,
        slack_channel_id="test1_channel_id",
        ts="test1_ts",
    )
    make_resolution_note_slack_message(
        alert_group=alert_group,
        user=user,
        added_by_user=user,
        added_to_resolution_note=True,
        slack_channel_id="test2_channel_id",
        ts="test2_ts",
    )

    with patch(
        "apps.alerts.tasks.delete_alert_group.send_alert_group_signal_for_delete.delay", return_value=None
    ) as mock_send_alert_group_signal:
        with django_capture_on_commit_callbacks(execute=True):
            delete_alert_group(alert_group.pk, user.pk)
    assert mock_send_alert_group_signal.call_count == 1

    with patch(
        "apps.alerts.tasks.delete_alert_group.finish_delete_alert_group.apply_async", return_value=None
    ) as mock_finish_delete_alert_group:
        with patch.object(
            SlackClient,
            api_method,
            side_effect=SlackAPIRatelimitError(
                response=build_slack_response({"ok": False, "error": "ratelimited"}, headers={"Retry-After": 42})
            ),
        ):
            send_alert_group_signal_for_delete(*mock_send_alert_group_signal.call_args.args)

    assert mock_finish_delete_alert_group.call_count == 0

    # Check task is retried gracefully
    mock_send_alert_group_signal_for_delete.assert_called_once_with(
        mock_send_alert_group_signal.call_args.args, countdown=42
    )


@pytest.mark.parametrize("api_method", ["reactions_remove", "chat_delete"])
@patch.object(delete_alert_group, "apply_async")
@pytest.mark.django_db
def test_delete_slack_api_error_other_than_ratelimit(
    mock_delete_alert_group,
    api_method,
    make_organization_with_slack_team_identity,
    make_user,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_slack_message,
    make_resolution_note_slack_message,
):
    organization, slack_team_identity = make_organization_with_slack_team_identity()
    user = make_user(organization=organization)

    alert_receive_channel = make_alert_receive_channel(organization)

    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group, raw_request_data={})

    # Create Slack messages
    make_slack_message(alert_group=alert_group, channel_id="test_channel_id", slack_id="test_slack_id")
    make_resolution_note_slack_message(
        alert_group=alert_group,
        user=user,
        added_by_user=user,
        posted_by_bot=True,
        slack_channel_id="test1_channel_id",
        ts="test1_ts",
    )
    make_resolution_note_slack_message(
        alert_group=alert_group,
        user=user,
        added_by_user=user,
        added_to_resolution_note=True,
        slack_channel_id="test2_channel_id",
        ts="test2_ts",
    )

    with patch.object(
        SlackClient,
        api_method,
        side_effect=SlackAPIMessageNotFoundError(
            response=build_slack_response({"ok": False, "error": "message_not_found"})
        ),
    ):
        delete_alert_group(alert_group.pk, user.pk)  # check no exception is raised

    # Check task is not retried
    mock_delete_alert_group.assert_not_called()


@pytest.mark.django_db
def test_alerts_count_gt(
    make_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)

    alert_group = make_alert_group(alert_receive_channel)

    # Check case when there is no alerts
    assert alert_group.alerts_count_gt(1) is False

    make_alert(alert_group, raw_request_data={})
    make_alert(alert_group, raw_request_data={})

    assert alert_group.alerts_count_gt(1) is True
    assert alert_group.alerts_count_gt(2) is False
    assert alert_group.alerts_count_gt(3) is False


@patch("apps.alerts.models.AlertGroup.start_unsilence_task", return_value=None)
@pytest.mark.django_db
def test_silence_by_user_for_period(
    mocked_start_unsilence_task,
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
):
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)

    alert_group = make_alert_group(alert_receive_channel)

    raw_next_step_eta = "2023-08-28T09:27:26.627047Z"
    silence_delay = 120 * 60
    updated_raw_next_step_eta = "2023-08-28T11:27:36.627047Z"  # silence_delay + START_ESCALATION_DELAY

    alert_group.raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()
    alert_group.raw_escalation_snapshot["next_step_eta"] = raw_next_step_eta

    assert not alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_SILENCE,
        author=user,
    ).exists()

    alert_group.silence_by_user_or_backsync(user, silence_delay=silence_delay)

    assert alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_SILENCE,
        author=user,
    ).exists()

    alert_group.refresh_from_db()

    assert alert_group.silenced
    assert alert_group.raw_escalation_snapshot["next_step_eta"] == updated_raw_next_step_eta
    assert mocked_start_unsilence_task.called


@patch("apps.alerts.models.AlertGroup.start_unsilence_task", return_value=None)
@pytest.mark.django_db
def test_silence_by_user_forever(
    mocked_start_unsilence_task,
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
):
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)

    alert_group = make_alert_group(alert_receive_channel)

    raw_next_step_eta = "2023-08-28T09:27:26.627047Z"

    alert_group.raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()
    alert_group.raw_escalation_snapshot["next_step_eta"] = raw_next_step_eta

    assert not alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_SILENCE,
        author=user,
    ).exists()

    alert_group.silence_by_user_or_backsync(user, silence_delay=None)

    assert alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_SILENCE,
        author=user,
    ).exists()

    alert_group.refresh_from_db()

    assert alert_group.silenced
    assert alert_group.raw_escalation_snapshot["next_step_eta"] == raw_next_step_eta
    assert not mocked_start_unsilence_task.called


@patch("apps.alerts.models.AlertGroup.start_unsilence_task", return_value=None)
@pytest.mark.django_db
def test_bulk_silence_for_period(
    mocked_start_unsilence_task,
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
):
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)

    alert_group = make_alert_group(alert_receive_channel)

    raw_next_step_eta = "2023-08-28T09:27:26.627047Z"
    silence_delay = 120 * 60
    updated_raw_next_step_eta = "2023-08-28T11:27:36.627047Z"  # silence_delay + START_ESCALATION_DELAY

    alert_group.raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()
    alert_group.raw_escalation_snapshot["next_step_eta"] = raw_next_step_eta
    alert_group.save()

    alert_groups = AlertGroup.objects.filter(pk__in=[alert_group.id])

    assert not alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_SILENCE,
        author=user,
    ).exists()

    AlertGroup.bulk_silence(user, alert_groups, silence_delay=silence_delay)

    assert alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_SILENCE,
        author=user,
    ).exists()

    alert_group.refresh_from_db()

    assert alert_group.silenced
    assert alert_group.raw_escalation_snapshot["next_step_eta"] == updated_raw_next_step_eta
    assert mocked_start_unsilence_task.called


@patch("apps.alerts.models.AlertGroup.start_unsilence_task", return_value=None)
@pytest.mark.django_db
def test_bulk_silence_forever(
    mocked_start_unsilence_task,
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
):
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)

    alert_group = make_alert_group(alert_receive_channel)

    raw_next_step_eta = "2023-08-28T09:27:26.627047Z"

    alert_group.raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()
    alert_group.raw_escalation_snapshot["next_step_eta"] = raw_next_step_eta
    alert_group.save()

    alert_groups = AlertGroup.objects.filter(pk__in=[alert_group.id])

    assert not alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_SILENCE,
        author=user,
    ).exists()

    AlertGroup.bulk_silence(user, alert_groups, silence_delay=0)

    assert alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_SILENCE,
        author=user,
    ).exists()

    alert_group.refresh_from_db()

    assert alert_group.silenced
    assert alert_group.raw_escalation_snapshot["next_step_eta"] == raw_next_step_eta
    assert not mocked_start_unsilence_task.called


@pytest.mark.parametrize("action_source", ActionSource)
@pytest.mark.django_db
def test_alert_group_log_record_action_source(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
    action_source,
):
    """Test that action source is saved in alert group log record"""
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)

    alert_group = make_alert_group(alert_receive_channel)
    root_alert_group = make_alert_group(alert_receive_channel)

    if action_source == ActionSource.BACKSYNC:
        base_kwargs = {
            "source_channel": alert_receive_channel,
        }
    else:
        base_kwargs = {
            "user": user,
        }

    # Silence alert group
    alert_group.silence_by_user_or_backsync(**base_kwargs, silence_delay=42, action_source=action_source)
    log_record = alert_group.log_records.last()
    assert (log_record.type, log_record.action_source) == (AlertGroupLogRecord.TYPE_SILENCE, action_source)

    # Unsilence alert group
    alert_group.un_silence_by_user_or_backsync(**base_kwargs, action_source=action_source)
    log_record = alert_group.log_records.last()
    assert (log_record.type, log_record.action_source) == (AlertGroupLogRecord.TYPE_UN_SILENCE, action_source)

    # Acknowledge alert group
    alert_group.acknowledge_by_user_or_backsync(**base_kwargs, action_source=action_source)
    log_record = alert_group.log_records.last()
    assert (log_record.type, log_record.action_source) == (AlertGroupLogRecord.TYPE_ACK, action_source)

    # Unacknowledge alert group
    alert_group.un_acknowledge_by_user_or_backsync(**base_kwargs, action_source=action_source)
    log_record = alert_group.log_records.last()
    assert (log_record.type, log_record.action_source) == (AlertGroupLogRecord.TYPE_UN_ACK, action_source)

    # Resolve alert group
    alert_group.resolve_by_user_or_backsync(**base_kwargs, action_source=action_source)
    log_record = alert_group.log_records.last()
    assert (log_record.type, log_record.action_source) == (AlertGroupLogRecord.TYPE_RESOLVED, action_source)

    # Unresolve alert group
    alert_group.un_resolve_by_user_or_backsync(**base_kwargs, action_source=action_source)
    log_record = alert_group.log_records.last()
    assert (log_record.type, log_record.action_source) == (AlertGroupLogRecord.TYPE_UN_RESOLVED, action_source)

    if action_source != ActionSource.BACKSYNC:
        # Attach alert group
        alert_group.attach_by_user(user, root_alert_group, action_source=action_source)
        log_record = alert_group.log_records.last()
        assert (log_record.type, log_record.action_source) == (AlertGroupLogRecord.TYPE_ATTACHED, action_source)

        # Unattach alert group
        alert_group.un_attach_by_user(user, action_source=action_source)
        log_record = alert_group.log_records.last()
        assert (log_record.type, log_record.action_source) == (AlertGroupLogRecord.TYPE_UNATTACHED, action_source)


@pytest.mark.django_db
def test_alert_group_get_paged_users(
    make_organization_and_user,
    make_user_for_organization,
    make_alert_receive_channel,
    make_alert_group,
):
    organization, user = make_organization_and_user()
    other_user = make_user_for_organization(organization)
    alert_receive_channel = make_alert_receive_channel(organization)

    def _make_log_record(alert_group, user, log_type, important=False):
        alert_group.log_records.create(
            type=log_type,
            author=user,
            reason="paged user",
            step_specific_info={
                "user": user.public_primary_key,
                "important": important,
            },
        )

    # user was paged - also check that important is persisted/available
    alert_group = make_alert_group(alert_receive_channel)
    _make_log_record(alert_group, user, AlertGroupLogRecord.TYPE_DIRECT_PAGING)
    _make_log_record(alert_group, other_user, AlertGroupLogRecord.TYPE_DIRECT_PAGING, True)

    paged_users = {u["pk"]: u["important"] for u in alert_group.get_paged_users()}

    assert user.public_primary_key in paged_users
    assert paged_users[user.public_primary_key] is False

    assert other_user.public_primary_key in paged_users
    assert paged_users[other_user.public_primary_key] is True

    # user was paged and then unpaged
    alert_group = make_alert_group(alert_receive_channel)
    _make_log_record(alert_group, user, AlertGroupLogRecord.TYPE_DIRECT_PAGING)
    _make_log_record(alert_group, user, AlertGroupLogRecord.TYPE_UNPAGE_USER)

    _make_log_record(alert_group, other_user, AlertGroupLogRecord.TYPE_DIRECT_PAGING)

    assert alert_group.get_paged_users()[0]["pk"] == other_user.public_primary_key

    # user was paged, unpaged, and then paged again - they should only show up once
    alert_group = make_alert_group(alert_receive_channel)
    _make_log_record(alert_group, user, AlertGroupLogRecord.TYPE_DIRECT_PAGING)
    _make_log_record(alert_group, user, AlertGroupLogRecord.TYPE_UNPAGE_USER)
    _make_log_record(alert_group, user, AlertGroupLogRecord.TYPE_DIRECT_PAGING)

    paged_users = alert_group.get_paged_users()
    assert len(paged_users) == 1
    assert alert_group.get_paged_users()[0]["pk"] == user.public_primary_key

    # user was paged and then paged again - they should only show up once
    alert_group = make_alert_group(alert_receive_channel)
    _make_log_record(alert_group, user, AlertGroupLogRecord.TYPE_DIRECT_PAGING)
    _make_log_record(alert_group, user, AlertGroupLogRecord.TYPE_DIRECT_PAGING)

    paged_users = alert_group.get_paged_users()
    assert len(paged_users) == 1
    assert alert_group.get_paged_users()[0]["pk"] == user.public_primary_key

    # user was paged and then paged again, then unpaged - they should not show up
    alert_group = make_alert_group(alert_receive_channel)
    _make_log_record(alert_group, user, AlertGroupLogRecord.TYPE_DIRECT_PAGING)
    _make_log_record(alert_group, user, AlertGroupLogRecord.TYPE_DIRECT_PAGING)
    _make_log_record(alert_group, user, AlertGroupLogRecord.TYPE_UNPAGE_USER)

    paged_users = alert_group.get_paged_users()
    assert len(paged_users) == 0

    # adding extra unpage events should not break things
    _make_log_record(alert_group, user, AlertGroupLogRecord.TYPE_UNPAGE_USER)
    _make_log_record(alert_group, user, AlertGroupLogRecord.TYPE_UNPAGE_USER)
    _make_log_record(alert_group, user, AlertGroupLogRecord.TYPE_DIRECT_PAGING)

    paged_users = alert_group.get_paged_users()
    assert len(paged_users) == 1
    assert alert_group.get_paged_users()[0]["pk"] == user.public_primary_key


@patch("apps.alerts.models.AlertGroup.start_unsilence_task", return_value=None)
@pytest.mark.django_db
def test_filter_active_alert_groups(
    mocked_start_unsilence_task,
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
):
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)

    # alert groups with active escalation
    alert_group_active = make_alert_group(alert_receive_channel)
    alert_group_active_silenced = make_alert_group(alert_receive_channel)
    alert_group_active_silenced.silence_by_user_or_backsync(user, silence_delay=1800)  # silence by period
    # alert groups with inactive escalation
    alert_group_1 = make_alert_group(alert_receive_channel)
    alert_group_1.acknowledge_by_user_or_backsync(user)
    alert_group_2 = make_alert_group(alert_receive_channel)
    alert_group_2.resolve_by_user_or_backsync(user)
    alert_group_3 = make_alert_group(alert_receive_channel)
    alert_group_3.attach_by_user(user, alert_group_active)
    alert_group_4 = make_alert_group(alert_receive_channel)
    alert_group_4.silence_by_user_or_backsync(user, silence_delay=None)  # silence forever

    active_alert_groups = AlertGroup.objects.filter_active()
    assert active_alert_groups.count() == 2
    assert alert_group_active in active_alert_groups
    assert alert_group_active_silenced in active_alert_groups


@patch("apps.alerts.models.AlertGroup.hard_delete")
@patch("apps.alerts.models.AlertGroup.un_attach_by_delete")
@patch("apps.alerts.models.AlertGroup.stop_escalation")
@patch("apps.alerts.tasks.delete_alert_group.alert_group_action_triggered_signal")
@pytest.mark.django_db
def test_delete_by_user(
    mock_alert_group_action_triggered_signal,
    _mock_stop_escalation,
    _mock_un_attach_by_delete,
    _mock_hard_delete,
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
    django_capture_on_commit_callbacks,
):
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)

    alert_group = make_alert_group(alert_receive_channel)

    # make a few dependent alert groups
    dependent_alert_groups = [make_alert_group(alert_receive_channel, root_alert_group=alert_group) for _ in range(3)]

    assert alert_group.log_records.filter(type=AlertGroupLogRecord.TYPE_DELETED).count() == 0

    with patch(
        "apps.alerts.tasks.delete_alert_group.send_alert_group_signal_for_delete.delay", return_value=None
    ) as mock_send_alert_group_signal:
        with django_capture_on_commit_callbacks(execute=True):
            delete_alert_group(alert_group.pk, user.pk)

    assert mock_send_alert_group_signal.call_count == 1
    assert alert_group.log_records.filter(type=AlertGroupLogRecord.TYPE_DELETED).count() == 1
    deleted_log_record = alert_group.log_records.get(type=AlertGroupLogRecord.TYPE_DELETED)
    alert_group.stop_escalation.assert_called_once_with()

    with patch(
        "apps.alerts.tasks.delete_alert_group.finish_delete_alert_group.apply_async", return_value=None
    ) as mock_finish_delete_alert_group:
        send_alert_group_signal_for_delete(*mock_send_alert_group_signal.call_args.args)
    assert mock_finish_delete_alert_group.call_count == 1

    mock_alert_group_action_triggered_signal.send.assert_called_once_with(
        sender=send_alert_group_signal_for_delete,
        log_record=deleted_log_record.pk,
        force_sync=True,
    )

    finish_delete_alert_group(alert_group.pk)

    alert_group.hard_delete.assert_called_once_with()

    for dependent_alert_group in dependent_alert_groups:
        dependent_alert_group.un_attach_by_delete.assert_called_with()


@pytest.mark.django_db
def test_integration_config_on_alert_group_created(make_organization, make_alert_receive_channel, make_channel_filter):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization, grouping_id_template="group_to_one_group")

    with patch.object(
        alert_receive_channel.config, "on_alert_group_created", create=True
    ) as mock_on_alert_group_created:
        for _ in range(2):
            alert = Alert.create(
                title="the title",
                message="the message",
                alert_receive_channel=alert_receive_channel,
                raw_request_data={},
                integration_unique_data={},
                image_url=None,
                link_to_upstream_details=None,
            )

    assert alert.group.alerts.count() == 2
    mock_on_alert_group_created.assert_called_once_with(alert.group)


@patch.object(AlertGroup, "start_escalation_if_needed")
@pytest.mark.django_db
@pytest.mark.parametrize(
    "new_state,log_type,to_firing_log_type",
    [
        (AlertGroupState.ACKNOWLEDGED, AlertGroupLogRecord.TYPE_ACK, AlertGroupLogRecord.TYPE_UN_ACK),
        (AlertGroupState.RESOLVED, AlertGroupLogRecord.TYPE_RESOLVED, AlertGroupLogRecord.TYPE_UN_RESOLVED),
        (AlertGroupState.SILENCED, AlertGroupLogRecord.TYPE_SILENCE, AlertGroupLogRecord.TYPE_UN_SILENCE),
    ],
)
def test_update_state_by_backsync(
    mock_start_escalation_if_needed,
    new_state,
    log_type,
    to_firing_log_type,
    make_organization,
    make_alert_receive_channel,
    make_alert_group,
):
    organization = make_organization()
    source_channel = make_alert_receive_channel(organization)
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    expected_log_data = (ActionSource.BACKSYNC, None, {"source_integration_name": source_channel.verbal_name})
    assert alert_group.state == AlertGroupState.FIRING
    # set to new_state
    alert_group.update_state_by_backsync(new_state, source_channel=source_channel)
    alert_group.refresh_from_db()
    assert alert_group.state == new_state
    last_log = alert_group.log_records.last()
    assert (last_log.action_source, last_log.author, last_log.step_specific_info) == expected_log_data
    assert last_log.type == log_type
    # set back to firing
    alert_group.update_state_by_backsync(AlertGroupState.FIRING, source_channel=source_channel)
    alert_group.refresh_from_db()
    assert alert_group.state == AlertGroupState.FIRING
    last_log = alert_group.log_records.last()
    assert (last_log.action_source, last_log.author, last_log.step_specific_info) == expected_log_data
    assert last_log.type == to_firing_log_type
    mock_start_escalation_if_needed.assert_called_once()


@pytest.mark.django_db
def test_alert_group_created_if_resolve_condition_but_auto_resolving_disabled(
    make_organization,
    make_alert_receive_channel,
    make_alert_group,
):
    organization = make_organization()
    # grouping condition will match. resolve condition will evaluate to True, but auto resolving is disabled
    grouping_distinction = "abcdef"
    alert_receive_channel = make_alert_receive_channel(
        organization,
        grouping_id_template=grouping_distinction,
        resolve_condition_template="True",
        allow_source_based_resolving=False,
    )
    # existing alert group, resolved, with a matching grouping distinction
    resolved_alert_group = make_alert_group(
        alert_receive_channel,
        resolved=True,
        distinction=hashlib.md5(grouping_distinction.encode()).hexdigest(),
    )

    # an alert for the same integration is received
    alert = Alert.create(
        title="the title",
        message="the message",
        alert_receive_channel=alert_receive_channel,
        raw_request_data={},
        integration_unique_data={},
        image_url=None,
        link_to_upstream_details=None,
    )

    # the alert will create a new alert group
    assert alert.group != resolved_alert_group
