from lib.opsgenie.report import (
    escalation_policy_report,
    format_escalation_policy,
    format_integration,
    format_schedule,
    format_user,
    integration_report,
    schedule_report,
    user_report,
)


def test_format_user():
    user = {
        "fullName": "John Doe",
        "username": "john.doe@example.com",
    }
    assert format_user(user) == "John Doe (john.doe@example.com)"


def test_format_schedule():
    schedule = {
        "name": "Primary Schedule",
    }
    assert format_schedule(schedule) == "Primary Schedule"


def test_format_escalation_policy():
    policy = {
        "name": "Critical Alerts",
        "ownerTeam": {
            "name": "Team A",
        },
    }
    assert format_escalation_policy(policy) == "Team A - Critical Alerts"


def test_format_integration():
    integration = {
        "name": "Prometheus Alerts",
        "type": "Prometheus",
    }
    assert format_integration(integration) == "Prometheus Alerts (Prometheus)"


def test_user_report():
    users = [
        {
            "fullName": "John Doe",
            "username": "john.doe@example.com",
            "oncall_user": {
                "notification_rules": [],
            },
        },
        {
            "fullName": "Jane Smith",
            "username": "jane.smith@example.com",
            "oncall_user": {
                "notification_rules": [{"id": "nr1"}],
            },
        },
        {
            "fullName": "Bob Wilson",
            "username": "bob.wilson@example.com",
            "oncall_user": None,
        },
    ]

    report = user_report(users)
    assert "✅ John Doe (john.doe@example.com)" in report
    assert (
        "⚠️ Jane Smith (jane.smith@example.com) (existing notification rules will be preserved)"
        in report
    )
    assert (
        "❌ Bob Wilson (bob.wilson@example.com) — no Grafana OnCall user found with this email"
        in report
    )


def test_schedule_report():
    schedules = [
        {
            "name": "Primary Schedule",
            "migration_errors": [],
            "oncall_schedule": None,
        },
        {
            "name": "Secondary Schedule",
            "migration_errors": [],
            "oncall_schedule": {"id": "os1"},
        },
        {
            "name": "Broken Schedule",
            "migration_errors": ["schedule references unmatched users"],
        },
    ]

    report = schedule_report(schedules)
    assert "✅ Primary Schedule" in report
    assert "⚠️ Secondary Schedule (existing schedule will be deleted)" in report
    assert "❌ Broken Schedule — schedule references unmatched users" in report


def test_escalation_policy_report():
    policies = [
        {
            "name": "Critical Alerts",
            "oncall_escalation_chain": None,
            "ownerTeam": {
                "name": "Team A",
            },
        },
        {
            "name": "Non-Critical Alerts",
            "oncall_escalation_chain": {"id": "oc1"},
            "ownerTeam": {
                "name": "Team B",
            },
        },
    ]

    report = escalation_policy_report(policies)
    assert "✅ Team A - Critical Alerts" in report
    assert (
        "⚠️ Team B - Non-Critical Alerts (existing escalation chain will be deleted)"
        in report
    )


def test_integration_report():
    integrations = [
        {
            "name": "Prometheus Alerts",
            "type": "Prometheus",
            "oncall_integration": None,
            "oncall_type": "alertmanager",
        },
        {
            "name": "Datadog Alerts",
            "type": "Datadog",
            "oncall_integration": {"id": "oi1"},
            "oncall_type": "datadog",
        },
        {
            "name": "Custom Integration",
            "type": "Custom",
            "oncall_integration": None,
            "oncall_type": None,
        },
    ]

    report = integration_report(integrations)
    assert "✅ Prometheus Alerts (Prometheus)" in report
    assert (
        "⚠️ Datadog Alerts (Datadog) (existing integration will be deleted)" in report
    )
    assert "❌ Custom Integration (Custom) — unsupported integration type" in report
