import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.alerts.constants import ActionSource, AlertGroupState
from apps.alerts.models import AlertReceiveChannel
from apps.api.permissions import LegacyAccessControlRole
from apps.mattermost.events.types import EventAction
from apps.mattermost.models import MattermostMessage
from apps.mattermost.utils import MattermostEventAuthenticator


@pytest.mark.django_db
@pytest.mark.parametrize(
    "event_action,expected_state",
    [
        (EventAction.ACKNOWLEDGE, AlertGroupState.ACKNOWLEDGED),
        (EventAction.RESOLVE, AlertGroupState.RESOLVED),
        (EventAction.UNACKNOWLEDGE, AlertGroupState.FIRING),
        (EventAction.UNRESOLVE, AlertGroupState.FIRING),
    ],
)
def test_mattermost_alert_group_event_success(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_mattermost_channel,
    make_alert_group,
    make_alert,
    make_mattermost_event,
    make_mattermost_message,
    make_mattermost_user,
    event_action,
    expected_state,
):
    organization, user, _ = make_organization_and_user_with_plugin_token()

    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA
    )

    if event_action in [EventAction.ACKNOWLEDGE, EventAction.RESOLVE]:
        alert_group = make_alert_group(alert_receive_channel)
    elif event_action == EventAction.UNACKNOWLEDGE:
        alert_group = make_alert_group(
            alert_receive_channel=alert_receive_channel,
            acknowledged_at=timezone.now(),
            acknowledged=True,
        )
    elif event_action == EventAction.UNRESOLVE:
        alert_group = make_alert_group(alert_receive_channel, resolved=True)

    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)

    make_mattermost_channel(organization=organization, is_default_channel=True)
    mattermost_message = make_mattermost_message(alert_group, MattermostMessage.ALERT_GROUP_MESSAGE)
    mattermost_user = make_mattermost_user(user=user)

    token = MattermostEventAuthenticator.create_token(organization=organization)
    event = make_mattermost_event(
        event_action,
        token,
        post_id=mattermost_message.post_id,
        channel_id=mattermost_message.channel_id,
        user_id=mattermost_user.mattermost_user_id,
        alert=alert_group.public_primary_key,
    )

    url = reverse("mattermost:incoming_mattermost_event")
    client = APIClient()
    response = client.post(url, event, format="json")
    alert_group.refresh_from_db()
    assert alert_group.state == expected_state
    assert alert_group.log_records.last().action_source == ActionSource.MATTERMOST
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_mattermost_alert_group_event_incorrect_token(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_mattermost_channel,
    make_alert_group,
    make_alert,
    make_mattermost_event,
    make_mattermost_message,
    make_mattermost_user,
):
    organization, user, _ = make_organization_and_user_with_plugin_token()

    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA
    )
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)

    make_mattermost_channel(organization=organization, is_default_channel=True)
    mattermost_message = make_mattermost_message(alert_group, MattermostMessage.ALERT_GROUP_MESSAGE)
    mattermost_user = make_mattermost_user(user=user)

    token = MattermostEventAuthenticator.create_token(organization=organization)
    token += "abx"
    event = make_mattermost_event(
        EventAction.ACKNOWLEDGE,
        token,
        post_id=mattermost_message.post_id,
        channel_id=mattermost_message.channel_id,
        user_id=mattermost_user.mattermost_user_id,
        alert=alert_group.public_primary_key,
    )

    url = reverse("mattermost:incoming_mattermost_event")
    client = APIClient()
    response = client.post(url, event, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_mattermost_alert_group_event_insufficient_permission(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_mattermost_channel,
    make_alert_group,
    make_alert,
    make_mattermost_event,
    make_mattermost_message,
    make_mattermost_user,
):
    organization, user, _ = make_organization_and_user_with_plugin_token(LegacyAccessControlRole.VIEWER)

    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA
    )
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)

    make_mattermost_channel(organization=organization, is_default_channel=True)
    mattermost_message = make_mattermost_message(alert_group, MattermostMessage.ALERT_GROUP_MESSAGE)
    mattermost_user = make_mattermost_user(user=user)

    token = MattermostEventAuthenticator.create_token(organization=organization)
    event = make_mattermost_event(
        EventAction.ACKNOWLEDGE,
        token,
        post_id=mattermost_message.post_id,
        channel_id=mattermost_message.channel_id,
        user_id=mattermost_user.mattermost_user_id,
        alert=alert_group.public_primary_key,
    )

    url = reverse("mattermost:incoming_mattermost_event")
    client = APIClient()
    response = client.post(url, event, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN
