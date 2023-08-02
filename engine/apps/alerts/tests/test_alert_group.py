import pytest

from apps.alerts.incident_appearance.renderers.phone_call_renderer import AlertGroupPhoneCallRenderer
from apps.alerts.models import AlertGroup
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
