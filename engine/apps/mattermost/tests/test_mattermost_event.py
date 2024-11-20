import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.alerts.models import AlertReceiveChannel
from apps.api.permissions import LegacyAccessControlRole
from apps.mattermost.events.types import EventAction
from apps.mattermost.models import MattermostMessage
from apps.mattermost.utils import MattermostEventAuthenticator


@pytest.mark.django_db
def test_mattermost_alert_group_event_acknowledge(
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
    event = make_mattermost_event(
        EventAction.ACKNOWLEDGE,
        token,
        post_id=mattermost_message.post_id,
        channel_id=mattermost_message.channel_id,
        user_id=mattermost_user.mattermost_user_id,
        alert=alert_group.pk,
    )

    url = reverse("mattermost:incoming_mattermost_event")
    client = APIClient()
    response = client.post(url, event, format="json")
    alert_group.refresh_from_db()
    assert alert_group.acknowledged
    assert not alert_group.resolved
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_mattermost_alert_group_event_unacknowledge(
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
    alert_group = make_alert_group(
        alert_receive_channel=alert_receive_channel,
        acknowledged_at=timezone.now(),
        acknowledged=True,
    )
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)

    make_mattermost_channel(organization=organization, is_default_channel=True)
    mattermost_message = make_mattermost_message(alert_group, MattermostMessage.ALERT_GROUP_MESSAGE)
    mattermost_user = make_mattermost_user(user=user)

    token = MattermostEventAuthenticator.create_token(organization=organization)
    event = make_mattermost_event(
        EventAction.UNACKNOWLEDGE,
        token,
        post_id=mattermost_message.post_id,
        channel_id=mattermost_message.channel_id,
        user_id=mattermost_user.mattermost_user_id,
        alert=alert_group.pk,
    )

    url = reverse("mattermost:incoming_mattermost_event")
    client = APIClient()
    response = client.post(url, event, format="json")
    alert_group.refresh_from_db()
    assert not alert_group.acknowledged
    assert not alert_group.resolved
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_mattermost_alert_group_event_resolve(
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
    event = make_mattermost_event(
        EventAction.RESOLVE,
        token,
        post_id=mattermost_message.post_id,
        channel_id=mattermost_message.channel_id,
        user_id=mattermost_user.mattermost_user_id,
        alert=alert_group.pk,
    )

    url = reverse("mattermost:incoming_mattermost_event")
    client = APIClient()
    response = client.post(url, event, format="json")
    alert_group.refresh_from_db()
    assert not alert_group.acknowledged
    assert alert_group.resolved
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_mattermost_alert_group_event_unresolve(
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
    alert_group = make_alert_group(alert_receive_channel, resolved=True)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)

    make_mattermost_channel(organization=organization, is_default_channel=True)
    mattermost_message = make_mattermost_message(alert_group, MattermostMessage.ALERT_GROUP_MESSAGE)
    mattermost_user = make_mattermost_user(user=user)

    token = MattermostEventAuthenticator.create_token(organization=organization)
    event = make_mattermost_event(
        EventAction.UNRESOLVE,
        token,
        post_id=mattermost_message.post_id,
        channel_id=mattermost_message.channel_id,
        user_id=mattermost_user.mattermost_user_id,
        alert=alert_group.pk,
    )

    url = reverse("mattermost:incoming_mattermost_event")
    client = APIClient()
    response = client.post(url, event, format="json")
    alert_group.refresh_from_db()
    assert not alert_group.acknowledged
    assert not alert_group.resolved
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
        alert=alert_group.pk,
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
        alert=alert_group.pk,
    )

    url = reverse("mattermost:incoming_mattermost_event")
    client = APIClient()
    response = client.post(url, event, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN
