import pytest

from apps.alerts.models.alert_manager_models import AlertForAlertManager, AlertGroupForAlertManager


@pytest.mark.django_db
def test_hash_based_on_labels():
    alert_a = AlertForAlertManager(
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
        }
    )

    alert_b = AlertForAlertManager(
        raw_request_data={
            "status": "firing",
            "labels": {
                "alertname": "TestAlert",
                "region": "us-east",
            },
            "annotations": {},
            "startsAt": "2018-12-25T15:47:47.377363608Z",
            "endsAt": "0001-01-01T00:00:00Z",
            "generatorURL": "",
        }
    )

    assert alert_a.get_integration_optimization_hash() != alert_b.get_integration_optimization_hash()

    alert_c = AlertForAlertManager(
        raw_request_data={
            "status": "firing",
            "labels": {
                "alertname": "TestAlert",
                "region": "us-east",
            },
            "annotations": {},
            "startsAt": "2018-12-25T15:47:47.377363608Z",
            "endsAt": "another time",
            "generatorURL": "",
        }
    )

    assert alert_b.get_integration_optimization_hash() == alert_c.get_integration_optimization_hash()


@pytest.mark.django_db
def test_alert_group_resolved(
    make_organization, make_slack_team_identity, make_escalation_chain, make_channel_filter, make_alert_receive_channel
):
    team_identity = make_slack_team_identity()
    organization = make_organization(slack_team_identity=team_identity)

    alert_receive_channel = make_alert_receive_channel(organization)
    escalation_chain = make_escalation_chain(organization)
    make_channel_filter(alert_receive_channel, escalation_chain=escalation_chain)

    alert_group = AlertGroupForAlertManager(channel=alert_receive_channel)
    alert_group.save()

    alert_a = AlertForAlertManager(
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
        group=alert_group,
    )
    alert_a.save()

    alert_b = AlertForAlertManager(
        raw_request_data={
            "status": "firing",
            "labels": {
                "alertname": "TestAlert",
                "region": "us-east",
            },
            "annotations": {},
            "startsAt": "2018-12-25T15:47:47.377363608Z",
            "endsAt": "0001-01-01T00:00:00Z",
            "generatorURL": "",
        },
        group=alert_group,
    )
    alert_b.save()

    alert_a_resolve = AlertForAlertManager(
        raw_request_data={
            "status": "resolved",
            "labels": {
                "region": "eu-1",
                "alertname": "TestAlert",
            },
            "annotations": {},
            "startsAt": "2018-12-25T15:47:47.377363608Z",
            "endsAt": "another time",
            "generatorURL": "",
        },
        group=alert_group,
    )

    assert alert_group.is_alert_a_resolve_signal(alert_a_resolve) is False
    alert_a_resolve.save()

    alert_b_resolve = AlertForAlertManager(
        raw_request_data={
            "status": "resolved",
            "labels": {
                "alertname": "TestAlert",
                "region": "us-east",
            },
            "annotations": {},
            "startsAt": "2018-12-25T15:47:47.377363608Z",
            "endsAt": "0001-01-01T00:00:00Z",
            "generatorURL": "",
        },
        group=alert_group,
    )
    alert_b_resolve.save()

    assert alert_group.is_alert_a_resolve_signal(alert_b_resolve) is True
