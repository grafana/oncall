from unittest.mock import patch

import httpretty
import pytest

from apps.alerts.models import AlertGroupLogRecord, EscalationPolicy, RelatedIncident
from apps.alerts.tasks.declare_incident import (
    ATTACHMENT_CAPTION,
    DEFAULT_BACKUP_TITLE,
    DEFAULT_INCIDENT_SEVERITY,
    ERROR_SEVERITY_NOT_FOUND,
    MAX_ATTACHED_ALERT_GROUPS_PER_INCIDENT,
    declare_incident,
)
from common.incident_api.client import IncidentAPIException


@pytest.fixture
def setup_alert_group_and_escalation_step(
    make_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_channel_filter,
    make_escalation_chain,
    make_escalation_policy,
):
    def _setup_alert_group_and_escalation_step(is_default_route=False, already_declared_incident=False):
        organization = make_organization(grafana_url="https://stack.grafana.net", api_token="token")
        alert_receive_channel = make_alert_receive_channel(organization=organization)
        escalation_chain = make_escalation_chain(organization)
        declare_incident_step = make_escalation_policy(
            escalation_chain=escalation_chain,
            escalation_policy_step=EscalationPolicy.STEP_DECLARE_INCIDENT,
        )
        channel_filter = make_channel_filter(
            alert_receive_channel,
            escalation_chain=escalation_chain,
            is_default=is_default_route,
        )
        alert_group = make_alert_group(
            alert_receive_channel=alert_receive_channel,
            channel_filter=channel_filter,
        )
        declared_incident = None
        if already_declared_incident:
            declared_incident = RelatedIncident.objects.create(
                incident_id="123",
                organization=organization,
                channel_filter=channel_filter,
            )

        return alert_group, declare_incident_step, declared_incident

    return _setup_alert_group_and_escalation_step


@pytest.mark.django_db
def test_declare_incident_default_route(setup_alert_group_and_escalation_step):
    alert_group, declare_incident_step, _ = setup_alert_group_and_escalation_step(is_default_route=True)

    declare_incident(alert_group.pk, declare_incident_step.pk)

    alert_group.refresh_from_db()
    # check triggered log
    log_record = alert_group.log_records.last()
    assert log_record.type == log_record.TYPE_ESCALATION_FAILED
    assert log_record.escalation_policy == declare_incident_step
    assert log_record.escalation_policy_step == EscalationPolicy.STEP_DECLARE_INCIDENT
    assert log_record.step_specific_info is None
    assert log_record.reason == "Declare incident step is not enabled for default routes"
    assert log_record.escalation_error_code == AlertGroupLogRecord.ERROR_ESCALATION_INCIDENT_COULD_NOT_BE_DECLARED


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_declare_incident_ok(setup_alert_group_and_escalation_step):
    alert_group, declare_incident_step, _ = setup_alert_group_and_escalation_step(already_declared_incident=False)

    with patch("common.incident_api.client.IncidentAPIClient.create_incident") as mock_create_incident:
        mock_create_incident.return_value = {"incidentID": "123", "title": "Incident"}, None
        declare_incident(alert_group.pk, declare_incident_step.pk)

    mock_create_incident.assert_called_with(
        DEFAULT_BACKUP_TITLE,
        severity=DEFAULT_INCIDENT_SEVERITY,
        attachCaption=ATTACHMENT_CAPTION,
        attachURL=alert_group.web_link,
    )

    alert_group.refresh_from_db()

    # check declared incident
    new_incident = alert_group.related_incidents.get()
    assert new_incident.incident_id == "123"
    assert new_incident.organization == alert_group.channel.organization
    assert new_incident.channel_filter == alert_group.channel_filter
    # check triggered log
    log_record = alert_group.log_records.last()
    assert log_record.type == log_record.TYPE_ESCALATION_TRIGGERED
    assert log_record.escalation_policy == declare_incident_step
    assert log_record.escalation_policy_step == EscalationPolicy.STEP_DECLARE_INCIDENT
    assert log_record.step_specific_info == {"incident_id": "123", "incident_title": "Incident"}
    assert log_record.reason == "incident declared"
    assert log_record.escalation_error_code is None


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_declare_incident_set_severity(setup_alert_group_and_escalation_step):
    alert_group, declare_incident_step, _ = setup_alert_group_and_escalation_step(already_declared_incident=False)
    severity = "critical"

    with patch("common.incident_api.client.IncidentAPIClient.create_incident") as mock_create_incident:
        mock_create_incident.return_value = {"incidentID": "123", "title": "Incident"}, None
        declare_incident(alert_group.pk, declare_incident_step.pk, severity=severity)

    mock_create_incident.assert_called_with(
        DEFAULT_BACKUP_TITLE, severity=severity, attachCaption=ATTACHMENT_CAPTION, attachURL=alert_group.web_link
    )


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_declare_incident_set_severity_from_label(setup_alert_group_and_escalation_step):
    alert_group, declare_incident_step, _ = setup_alert_group_and_escalation_step(already_declared_incident=False)
    expected_severity = "minor"
    # set alert group label
    alert_group.labels.create(
        organization=alert_group.channel.organization, key_name="severity", value_name=expected_severity
    )
    severity = EscalationPolicy.SEVERITY_SET_FROM_LABEL

    with patch("common.incident_api.client.IncidentAPIClient.create_incident") as mock_create_incident:
        mock_create_incident.return_value = {"incidentID": "123", "title": "Incident"}, None
        declare_incident(alert_group.pk, declare_incident_step.pk, severity=severity)

    mock_create_incident.assert_called_with(
        DEFAULT_BACKUP_TITLE,
        severity=expected_severity,
        attachCaption=ATTACHMENT_CAPTION,
        attachURL=alert_group.web_link,
    )


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_declare_incident_invalid_severity_fallback(setup_alert_group_and_escalation_step):
    alert_group, declare_incident_step, _ = setup_alert_group_and_escalation_step(already_declared_incident=False)
    severity = "INVALID"

    with patch("common.incident_api.client.IncidentAPIClient.create_incident") as mock_create_incident:
        with patch.object(declare_incident, "apply_async") as mock_declare_incident_apply_async:
            mock_create_incident.side_effect = IncidentAPIException(
                status=500, url="some-url", msg=ERROR_SEVERITY_NOT_FOUND
            )
            declare_incident(alert_group.pk, declare_incident_step.pk, severity=severity)

    # create call failing with invalid severity
    mock_create_incident.assert_called_with(
        DEFAULT_BACKUP_TITLE, severity=severity, attachCaption=ATTACHMENT_CAPTION, attachURL=alert_group.web_link
    )
    # new task is queued with default severity instead
    mock_declare_incident_apply_async.assert_called_with(
        args=(alert_group.pk, declare_incident_step.pk), kwargs={"severity": DEFAULT_INCIDENT_SEVERITY}
    )


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_declare_incident_attach_alert_group(setup_alert_group_and_escalation_step):
    alert_group, declare_incident_step, existing_open_incident = setup_alert_group_and_escalation_step(
        already_declared_incident=True
    )
    incident_id = existing_open_incident.incident_id

    with patch("common.incident_api.client.IncidentAPIClient.get_incident") as mock_get_incident:
        with patch("common.incident_api.client.IncidentAPIClient.add_activity") as mock_add_activity:
            mock_get_incident.return_value = {"incidentID": incident_id, "title": "Incident", "status": "active"}, None
            mock_add_activity.return_value = {"activityItemID": "111"}, None
            declare_incident(alert_group.pk, declare_incident_step.pk)

    # check declared incident
    assert existing_open_incident.attached_alert_groups.filter(id=alert_group.id).exists()
    log_record = alert_group.log_records.last()
    assert log_record.type == log_record.TYPE_ESCALATION_TRIGGERED
    assert log_record.escalation_policy == declare_incident_step
    assert log_record.escalation_policy_step == EscalationPolicy.STEP_DECLARE_INCIDENT
    assert log_record.step_specific_info == {"incident_id": incident_id, "incident_title": "Incident"}
    assert log_record.reason == "attached to existing incident"
    assert log_record.escalation_error_code is None


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_declare_incident_resolved_update(setup_alert_group_and_escalation_step):
    alert_group, declare_incident_step, existing_open_incident = setup_alert_group_and_escalation_step(
        already_declared_incident=True
    )
    incident_id = existing_open_incident.incident_id
    new_incident_id = "333"
    assert new_incident_id != incident_id

    with patch("common.incident_api.client.IncidentAPIClient.get_incident") as mock_get_incident:
        with patch("common.incident_api.client.IncidentAPIClient.create_incident") as mock_create_incident:
            mock_get_incident.return_value = {
                "incidentID": incident_id,
                "title": "Incident1",
                "status": "resolved",
            }, None
            mock_create_incident.return_value = {"incidentID": new_incident_id, "title": "Incident2"}, None
            declare_incident(alert_group.pk, declare_incident_step.pk)

    existing_open_incident.refresh_from_db()

    assert existing_open_incident.is_active is False
    # check declared incident
    assert not existing_open_incident.attached_alert_groups.filter(id=alert_group.id).exists()
    assert alert_group.related_incidents.get().incident_id == new_incident_id
    log_record = alert_group.log_records.last()
    assert log_record.type == log_record.TYPE_ESCALATION_TRIGGERED
    assert log_record.escalation_policy == declare_incident_step
    assert log_record.escalation_policy_step == EscalationPolicy.STEP_DECLARE_INCIDENT
    assert log_record.step_specific_info == {"incident_id": new_incident_id, "incident_title": "Incident2"}
    assert log_record.reason == "incident declared"
    assert log_record.escalation_error_code is None


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_declare_incident_attach_alert_group_skip_incident_update(
    setup_alert_group_and_escalation_step, make_alert_group
):
    alert_group, declare_incident_step, existing_open_incident = setup_alert_group_and_escalation_step(
        already_declared_incident=True
    )
    alert_receive_channel = alert_group.channel
    channel_filter = alert_group.channel_filter
    incident_id = existing_open_incident.incident_id

    # attach max alert groups to incident
    for _ in range(MAX_ATTACHED_ALERT_GROUPS_PER_INCIDENT):
        ag = make_alert_group(alert_receive_channel=alert_receive_channel, channel_filter=channel_filter)
        existing_open_incident.attached_alert_groups.add(ag)

    with patch("common.incident_api.client.IncidentAPIClient.get_incident") as mock_get_incident:
        with patch("common.incident_api.client.IncidentAPIClient.add_activity") as mock_add_activity:
            mock_get_incident.return_value = {"incidentID": incident_id, "title": "Incident", "status": "active"}, None
            declare_incident(alert_group.pk, declare_incident_step.pk)

    assert not mock_add_activity.called

    # check declared incident
    assert existing_open_incident.attached_alert_groups.filter(id=alert_group.id).exists()
    log_record = alert_group.log_records.last()
    assert log_record.type == log_record.TYPE_ESCALATION_TRIGGERED
    assert log_record.escalation_policy == declare_incident_step
    assert log_record.escalation_policy_step == EscalationPolicy.STEP_DECLARE_INCIDENT
    assert log_record.step_specific_info == {"incident_id": incident_id, "incident_title": "Incident"}
    assert log_record.reason == "attached to existing incident"
    assert log_record.escalation_error_code is None


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_get_existing_incident_error(setup_alert_group_and_escalation_step):
    alert_group, declare_incident_step, existing_open_incident = setup_alert_group_and_escalation_step(
        already_declared_incident=True
    )

    with patch("common.incident_api.client.IncidentAPIClient.get_incident") as mock_get_incident:
        mock_get_incident.side_effect = IncidentAPIException(status=500, url="some-url")
        with pytest.raises(IncidentAPIException):
            declare_incident(alert_group.pk, declare_incident_step.pk)

    # but if incident was not found, a new one should be created
    incident_id = existing_open_incident.incident_id
    new_incident_id = "333"
    assert new_incident_id != incident_id

    with patch("common.incident_api.client.IncidentAPIClient.get_incident") as mock_get_incident:
        with patch("common.incident_api.client.IncidentAPIClient.create_incident") as mock_create_incident:
            mock_get_incident.side_effect = IncidentAPIException(status=404, url="some-url")
            mock_create_incident.return_value = {"incidentID": new_incident_id, "title": "Incident"}, None
            declare_incident(alert_group.pk, declare_incident_step.pk)

    alert_group.refresh_from_db()

    # check declared incident
    assert not existing_open_incident.attached_alert_groups.filter(id=alert_group.id).exists()
    new_incident = alert_group.related_incidents.get()
    assert new_incident != existing_open_incident
    assert new_incident.incident_id == new_incident_id
    assert new_incident.organization == alert_group.channel.organization
    assert new_incident.channel_filter == alert_group.channel_filter


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_attach_alert_group_error(setup_alert_group_and_escalation_step):
    alert_group, declare_incident_step, existing_open_incident = setup_alert_group_and_escalation_step(
        already_declared_incident=True
    )
    incident_id = existing_open_incident.incident_id

    with patch("common.incident_api.client.IncidentAPIClient.get_incident") as mock_get_incident:
        with patch("common.incident_api.client.IncidentAPIClient.add_activity") as mock_add_activity:
            mock_get_incident.return_value = {"incidentID": incident_id, "title": "Incident", "status": "active"}, None
            mock_add_activity.side_effect = IncidentAPIException(status=500, url="some-url")
            declare_incident(alert_group.pk, declare_incident_step.pk)

    alert_group.refresh_from_db()

    # incident attachment failed, but DB is still updated
    assert existing_open_incident.attached_alert_groups.filter(id=alert_group.id).exists()
    log_record = alert_group.log_records.last()
    assert log_record.type == log_record.TYPE_ESCALATION_TRIGGERED
    assert log_record.escalation_policy == declare_incident_step
    assert log_record.escalation_policy_step == EscalationPolicy.STEP_DECLARE_INCIDENT
    assert log_record.step_specific_info == {"incident_id": incident_id, "incident_title": "Incident"}
    assert log_record.reason == "attached to existing incident"
    assert log_record.escalation_error_code is None


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_create_incident_error(setup_alert_group_and_escalation_step):
    alert_group, declare_incident_step, _ = setup_alert_group_and_escalation_step(already_declared_incident=False)

    with patch("common.incident_api.client.IncidentAPIClient.create_incident") as mock_create_incident:
        mock_create_incident.side_effect = IncidentAPIException(status=500, url="some-url")
        with pytest.raises(IncidentAPIException):
            declare_incident(alert_group.pk, declare_incident_step.pk)
