from unittest.mock import call, patch

import pytest
from django.utils import timezone

from apps.alerts.models import AlertGroup, AlertGroupLogRecord
from apps.webhooks.models import Webhook
from apps.webhooks.tasks import alert_group_created, alert_group_status_change


@pytest.mark.django_db
def test_alert_group_created(make_organization, make_alert_receive_channel, make_alert_group, make_custom_webhook):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    # make sure there is a webhook setup
    make_custom_webhook(organization=organization, trigger_type=Webhook.TRIGGER_ALERT_GROUP_CREATED)

    with patch("apps.webhooks.tasks.trigger_webhook.send_webhook_event.apply_async") as mock_send_event:
        alert_group_created(alert_group.pk)

    assert mock_send_event.called
    assert mock_send_event.call_args == call(
        (Webhook.TRIGGER_ALERT_GROUP_CREATED, alert_group.pk),
        kwargs={"organization_id": organization.pk},
    )


@pytest.mark.django_db
def test_alert_group_created_for_team(
    make_organization, make_team, make_alert_receive_channel, make_alert_group, make_custom_webhook
):
    organization = make_organization()
    team = make_team(organization)
    alert_receive_channel = make_alert_receive_channel(organization, team=team)
    alert_group = make_alert_group(alert_receive_channel)
    # make sure there is a webhook setup
    make_custom_webhook(organization=organization, team=team, trigger_type=Webhook.TRIGGER_ALERT_GROUP_CREATED)

    with patch("apps.webhooks.tasks.trigger_webhook.send_webhook_event.apply_async") as mock_send_event:
        alert_group_created(alert_group.pk)

    assert mock_send_event.called
    assert mock_send_event.call_args == call(
        (Webhook.TRIGGER_ALERT_GROUP_CREATED, alert_group.pk),
        kwargs={"organization_id": organization.pk},
    )


@pytest.mark.django_db
def test_alert_group_created_does_not_exist(make_organization, make_custom_webhook):
    assert AlertGroup.objects.filter(pk=53).first() is None
    organization = make_organization()
    # make sure there is a webhook setup
    make_custom_webhook(organization=organization, trigger_type=Webhook.TRIGGER_ALERT_GROUP_CREATED)

    with patch("apps.webhooks.tasks.trigger_webhook.send_webhook_event.apply_async") as mock_send_event:
        alert_group_created(53)

    assert not mock_send_event.called


@pytest.mark.django_db
@pytest.mark.parametrize(
    "action_type,webhook_type",
    [
        (AlertGroupLogRecord.TYPE_ACK, Webhook.TRIGGER_ACKNOWLEDGE),
        (AlertGroupLogRecord.TYPE_RESOLVED, Webhook.TRIGGER_RESOLVE),
        (AlertGroupLogRecord.TYPE_SILENCE, Webhook.TRIGGER_SILENCE),
        (AlertGroupLogRecord.TYPE_UN_SILENCE, Webhook.TRIGGER_UNSILENCE),
        (AlertGroupLogRecord.TYPE_UN_RESOLVED, Webhook.TRIGGER_UNRESOLVE),
        (AlertGroupLogRecord.TYPE_UN_ACK, Webhook.TRIGGER_UNACKNOWLEDGE),
    ],
)
def test_alert_group_status_change(
    make_organization,
    make_user_for_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_custom_webhook,
    action_type,
    webhook_type,
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    # make sure there is a webhook setup
    make_custom_webhook(organization=organization, trigger_type=webhook_type)

    with patch("apps.webhooks.tasks.trigger_webhook.send_webhook_event.apply_async") as mock_send_event:
        alert_group_status_change(action_type, alert_group.pk, user.pk)

    assert mock_send_event.call_args == call(
        (webhook_type, alert_group.pk), kwargs={"organization_id": organization.pk, "user_id": user.pk}
    )


@pytest.mark.django_db
def test_alert_group_status_change_does_not_exist(make_organization, make_custom_webhook):
    assert AlertGroup.objects.filter(pk=53).first() is None
    organization = make_organization()
    # make sure there is a webhook setup
    make_custom_webhook(organization=organization, trigger_type=Webhook.TRIGGER_ACKNOWLEDGE)

    with patch("apps.webhooks.tasks.trigger_webhook.send_webhook_event.apply_async") as mock_send_event:
        alert_group_status_change(AlertGroupLogRecord.TYPE_ACK, 53, None)

    assert not mock_send_event.called


@pytest.mark.django_db
def test_alert_group_status_change_for_team(
    make_organization, make_team, make_alert_receive_channel, make_alert_group, make_custom_webhook
):
    organization = make_organization()
    team = make_team(organization)
    alert_receive_channel = make_alert_receive_channel(organization, team=team)
    alert_group = make_alert_group(alert_receive_channel, resolved=True, resolved_at=timezone.now())
    # make sure there is a webhook setup
    make_custom_webhook(organization=organization, team=team, trigger_type=Webhook.TRIGGER_RESOLVE)

    with patch("apps.webhooks.tasks.trigger_webhook.send_webhook_event.apply_async") as mock_send_event:
        alert_group_status_change(AlertGroupLogRecord.TYPE_RESOLVED, alert_group.pk, None)

    assert mock_send_event.call_args == call(
        (Webhook.TRIGGER_RESOLVE, alert_group.pk),
        kwargs={"organization_id": organization.pk, "user_id": None},
    )
