from unittest.mock import patch

import pytest

from apps.alerts.incident_appearance.renderers.phone_call_renderer import AlertGroupPhoneCallRenderer
from apps.alerts.models import AlertGroup, AlertGroupLogRecord
from apps.alerts.tasks.delete_alert_group import delete_alert_group
from apps.slack.models import SlackMessage


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
        f"Alert via {alert_receive_channel.verbal_name} - Grafana with title TestAlert triggered 1 times"
    )
    rendered_text = AlertGroupPhoneCallRenderer(alert_group).render()
    assert expected_verbose_name in rendered_text


@pytest.mark.django_db
def test_delete(
    make_organization_with_slack_team_identity,
    make_user,
    make_slack_channel,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
):
    """test alert group deleting"""

    organization, slack_team_identity = make_organization_with_slack_team_identity()
    slack_channel = make_slack_channel(slack_team_identity, name="general", slack_id="CWER1ASD")
    user = make_user(organization=organization)

    alert_receive_channel = make_alert_receive_channel(organization)

    alert_group = make_alert_group(alert_receive_channel)
    SlackMessage.objects.create(channel_id="CWER1ASD", alert_group=alert_group)

    make_alert(
        alert_group,
        raw_request_data={
            "evalMatches": [
                {"value": 100, "metric": "High value", "tags": None},
                {"value": 200, "metric": "Higher Value", "tags": None},
            ],
            "message": "Someone is testing the alert notification within grafana.",
            "ruleId": 0,
            "ruleName": "Test notification",
            "ruleUrl": "http://localhost:3000/",
            "state": "alerting",
            "title": f"Incident for channel <#{slack_channel.slack_id}> Where a > b & c < d",
        },
    )

    alerts = alert_group.alerts
    slack_messages = alert_group.slack_messages

    assert alerts.count() > 0
    assert slack_messages.count() > 0

    delete_alert_group(alert_group.pk, user.pk)

    assert alerts.count() == 0
    assert slack_messages.count() == 0

    with pytest.raises(AlertGroup.DoesNotExist):
        alert_group.refresh_from_db()


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

    alert_group.silence_by_user(user, silence_delay=silence_delay)

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

    alert_group.silence_by_user(user, silence_delay=None)

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
