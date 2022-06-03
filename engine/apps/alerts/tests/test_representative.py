import pytest

from apps.alerts.models import AlertGroupLogRecord, AlertReceiveChannel
from apps.slack.representatives.alert_group_representative import AlertGroupSlackRepresentative


@pytest.mark.django_db
def test_handler_escalation_triggered(
    make_organization_and_user,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_alert,
    make_alert_group_log_record,
):
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA
    )
    channel_filter = make_channel_filter(alert_receive_channel, is_default=True)

    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)
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
            "title": "[Alerting] Test notification",
        },
    )

    escalation_log_record = make_alert_group_log_record(
        alert_group, type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED, author=None
    )

    representative = AlertGroupSlackRepresentative(escalation_log_record)
    handler = representative.get_handler()
    assert handler.__name__ == "on_handler_not_found"
