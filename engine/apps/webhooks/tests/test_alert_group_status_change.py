from unittest.mock import call, patch

import pytest
from django.utils import timezone

from apps.alerts.models import AlertGroup, AlertGroupLogRecord
from apps.public_api.serializers import IncidentSerializer
from apps.webhooks.models import Webhook
from apps.webhooks.tasks import alert_group_created, alert_group_status_change


@pytest.mark.django_db
def test_alert_group_created(make_organization, make_alert_receive_channel, make_alert_group):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    with patch("apps.webhooks.tasks.trigger_webhook.send_webhook_event.apply_async") as mock_send_event:
        alert_group_created(alert_group.pk)

    assert mock_send_event.called
    expected_data = {
        "event": {
            "type": "Firing",
            "time": alert_group.started_at,
        },
        "user": None,
        "alert_group": IncidentSerializer(alert_group).data,
        "alert_group_id": alert_group.public_primary_key,
        "alert_payload": "",
    }

    assert mock_send_event.call_args == call(
        (Webhook.TRIGGER_NEW, expected_data), kwargs={"organization_id": organization.pk, "team_id": None}
    )


@pytest.mark.django_db
def test_alert_group_created_for_team(make_organization, make_team, make_alert_receive_channel, make_alert_group):
    organization = make_organization()
    team = make_team(organization)
    alert_receive_channel = make_alert_receive_channel(organization, team=team)
    alert_group = make_alert_group(alert_receive_channel)

    with patch("apps.webhooks.tasks.trigger_webhook.send_webhook_event.apply_async") as mock_send_event:
        alert_group_created(alert_group.pk)

    assert mock_send_event.called
    expected_data = {
        "event": {
            "type": "Firing",
            "time": alert_group.started_at,
        },
        "user": None,
        "alert_group": IncidentSerializer(alert_group).data,
        "alert_group_id": alert_group.public_primary_key,
        "alert_payload": "",
    }

    assert mock_send_event.call_args == call(
        (Webhook.TRIGGER_NEW, expected_data), kwargs={"organization_id": organization.pk, "team_id": team.pk}
    )


@pytest.mark.django_db
def test_alert_group_created_does_not_exist():
    assert AlertGroup.all_objects.filter(pk=53).first() is None

    with patch("apps.webhooks.tasks.trigger_webhook.send_webhook_event.apply_async") as mock_send_event:
        alert_group_created(53)

    assert not mock_send_event.called


@pytest.mark.django_db
@pytest.mark.parametrize(
    "action_type,event_type,webhook_type,time_field",
    [
        (AlertGroupLogRecord.TYPE_ACK, "Acknowledge", Webhook.TRIGGER_ACKNOWLEDGE, "acknowledged_at"),
        (AlertGroupLogRecord.TYPE_RESOLVED, "Resolve", Webhook.TRIGGER_RESOLVE, "resolved_at"),
        (AlertGroupLogRecord.TYPE_SILENCE, "Silence", Webhook.TRIGGER_SILENCE, "silenced_at"),
        (AlertGroupLogRecord.TYPE_UN_SILENCE, "Unsilence", Webhook.TRIGGER_UNSILENCE, None),
        (AlertGroupLogRecord.TYPE_UN_RESOLVED, "Unresolve", Webhook.TRIGGER_UNRESOLVE, None),
    ],
)
def test_alert_group_status_change(
    make_organization,
    make_user_for_organization,
    make_alert_receive_channel,
    make_alert_group,
    action_type,
    event_type,
    webhook_type,
    time_field,
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    with patch("apps.webhooks.tasks.trigger_webhook.send_webhook_event.apply_async") as mock_send_event:
        alert_group_status_change(action_type, alert_group.pk, user.pk)

    expected_data = {
        "event": {
            "type": event_type,
        },
        "user": user.username,
        "alert_group": IncidentSerializer(alert_group).data,
        "alert_group_id": alert_group.public_primary_key,
        "alert_payload": "",
    }
    if time_field is not None:
        expected_data["event"]["time"] = getattr(alert_group, time_field)
    if action_type == AlertGroupLogRecord.TYPE_SILENCE:
        expected_data["event"]["until"] = alert_group.silenced_until
    assert mock_send_event.call_args == call(
        (webhook_type, expected_data), kwargs={"organization_id": organization.pk, "team_id": None}
    )


@pytest.mark.django_db
def test_alert_group_status_change_does_not_exist():
    assert AlertGroup.all_objects.filter(pk=53).first() is None

    with patch("apps.webhooks.tasks.trigger_webhook.send_webhook_event.apply_async") as mock_send_event:
        alert_group_status_change(AlertGroupLogRecord.TYPE_ACK, 53, None)

    assert not mock_send_event.called


@pytest.mark.django_db
def test_alert_group_status_change_for_team(make_organization, make_team, make_alert_receive_channel, make_alert_group):
    organization = make_organization()
    team = make_team(organization)
    alert_receive_channel = make_alert_receive_channel(organization, team=team)
    alert_group = make_alert_group(alert_receive_channel, resolved=True, resolved_at=timezone.now())

    with patch("apps.webhooks.tasks.trigger_webhook.send_webhook_event.apply_async") as mock_send_event:
        alert_group_status_change(AlertGroupLogRecord.TYPE_RESOLVED, alert_group.pk, None)

    expected_data = {
        "event": {
            "type": "Resolve",
            "time": alert_group.resolved_at,
        },
        "user": None,
        "alert_group": IncidentSerializer(alert_group).data,
        "alert_group_id": alert_group.public_primary_key,
        "alert_payload": "",
    }
    assert mock_send_event.call_args == call(
        (Webhook.TRIGGER_RESOLVE, expected_data), kwargs={"organization_id": organization.pk, "team_id": team.pk}
    )
