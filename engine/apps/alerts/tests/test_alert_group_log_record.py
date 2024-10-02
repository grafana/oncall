from unittest.mock import patch

import pytest

from apps.alerts.models import AlertGroupLogRecord, EscalationPolicy
from apps.schedules.models import OnCallScheduleWeb


@pytest.mark.django_db
def test_skip_update_signal(
    make_organization_with_slack_team_identity,
    make_alert_receive_channel,
    make_alert_group,
):
    organization, _ = make_organization_with_slack_team_identity()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    for skip_type in AlertGroupLogRecord.TYPES_SKIPPING_UPDATE_SIGNAL:
        with patch("apps.alerts.tasks.send_update_log_report_signal") as mock_update_log_signal:
            alert_group.log_records.create(type=skip_type)
        assert not mock_update_log_signal.apply_async.called


@pytest.mark.django_db
def test_trigger_update_signal(
    make_organization_with_slack_team_identity,
    make_alert_receive_channel,
    make_alert_group,
):
    organization, _ = make_organization_with_slack_team_identity()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    for log_type, _ in AlertGroupLogRecord.TYPE_CHOICES:
        if log_type in AlertGroupLogRecord.TYPES_SKIPPING_UPDATE_SIGNAL:
            continue
        with patch("apps.alerts.tasks.send_update_log_report_signal") as mock_update_log_signal:
            alert_group.log_records.create(type=log_type)
        mock_update_log_signal.apply_async.assert_called_once()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "for_slack, html, substitute_with_tag, expected",
    [
        (True, False, False, 'with escalation chain "Escalation name"'),
        (False, True, False, 'with escalation chain "Escalation name"'),
        (False, False, True, 'with escalation chain "{{escalation_chain}}'),
    ],
)
def test_log_record_escalation_chain_link(
    make_organization_with_slack_team_identity,
    make_alert_receive_channel,
    make_escalation_chain,
    make_channel_filter,
    make_alert_group,
    for_slack,
    html,
    substitute_with_tag,
    expected,
):
    organization, _ = make_organization_with_slack_team_identity()
    alert_receive_channel = make_alert_receive_channel(organization)
    escalation_chain = make_escalation_chain(organization, name="Escalation name")
    channel_filter = make_channel_filter(alert_receive_channel, escalation_chain=escalation_chain)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)
    alert_group.raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()

    log = alert_group.log_records.create(
        type=AlertGroupLogRecord.TYPE_ROUTE_ASSIGNED,
    )

    log_line = log.rendered_log_line_action(for_slack=for_slack, html=html, substitute_with_tag=substitute_with_tag)
    assert expected in log_line

    log_data = log.render_log_line_json()
    escalation_chain_data = log_data.get("escalation_chain")
    assert escalation_chain_data == {"pk": escalation_chain.public_primary_key, "title": escalation_chain.name}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "for_slack, html, substitute_with_tag, expected",
    [
        (True, False, False, "Notify on-call from Schedule 'Schedule name'"),
        (False, True, False, "Notify on-call from Schedule 'Schedule name'"),
        (False, False, True, "Notify on-call from Schedule {{schedule}}"),
    ],
)
def test_log_record_schedule_link(
    make_organization_with_slack_team_identity,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_schedule,
    make_escalation_chain,
    make_escalation_policy,
    for_slack,
    html,
    substitute_with_tag,
    expected,
):
    organization, _ = make_organization_with_slack_team_identity()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb, name="Schedule name")
    escalation_chain = make_escalation_chain(organization, name="Escalation name")
    channel_filter = make_channel_filter(alert_receive_channel, escalation_chain=escalation_chain)
    escalation_policy = make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_SCHEDULE,
        notify_schedule=schedule,
    )

    log = alert_group.log_records.create(
        type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED,
        step_specific_info={"schedule_name": schedule.name},
        escalation_policy=escalation_policy,
    )

    log_line = log.rendered_log_line_action(for_slack=for_slack, html=html, substitute_with_tag=substitute_with_tag)
    assert expected in log_line

    log_data = log.render_log_line_json()
    schedule_data = log_data.get("schedule")
    assert schedule_data == {"pk": schedule.public_primary_key, "title": schedule.name}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "for_slack, html, substitute_with_tag, expected",
    [
        (True, False, False, "outgoing webhook `Webhook name`"),
        (False, True, False, "outgoing webhook `Webhook name`"),
        (False, False, True, "outgoing webhook `{{webhook}}`"),
    ],
)
def test_log_record_webhook_link(
    make_organization_with_slack_team_identity,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_custom_webhook,
    make_escalation_chain,
    make_escalation_policy,
    for_slack,
    html,
    substitute_with_tag,
    expected,
):
    organization, _ = make_organization_with_slack_team_identity()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    webhook = make_custom_webhook(organization, name="Webhook name")
    escalation_chain = make_escalation_chain(organization, name="Escalation name")
    channel_filter = make_channel_filter(alert_receive_channel, escalation_chain=escalation_chain)
    escalation_policy = make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_TRIGGER_CUSTOM_WEBHOOK,
        custom_webhook=webhook,
    )

    log = alert_group.log_records.create(
        type=AlertGroupLogRecord.TYPE_CUSTOM_WEBHOOK_TRIGGERED,
        step_specific_info={"webhook_id": webhook.public_primary_key, "webhook_name": webhook.name},
        escalation_policy=escalation_policy,
    )

    log_line = log.rendered_log_line_action(for_slack=for_slack, html=html, substitute_with_tag=substitute_with_tag)
    assert expected in log_line

    log_data = log.render_log_line_json()
    webhook_data = log_data.get("webhook")
    assert webhook_data == {"pk": webhook.public_primary_key, "title": webhook.name}
