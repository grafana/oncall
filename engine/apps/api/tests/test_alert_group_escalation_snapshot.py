import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.alerts.models import EscalationPolicy


@pytest.mark.django_db
def test_alert_group_escalation_snapshot_with_important(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_escalation_chain,
    make_escalation_policy,
    make_channel_filter,
    make_alert_group,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    escalation_chain = make_escalation_chain(organization)
    notify_to_multiple_users_step = make_escalation_policy(
        escalation_chain=escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS,
    )
    notify_to_multiple_users_step.notify_to_users_queue.set([user])
    notify_to_multiple_users_step_important = make_escalation_policy(
        escalation_chain=escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS_IMPORTANT,
    )
    notify_to_multiple_users_step_important.notify_to_users_queue.set([user])
    channel_filter = make_channel_filter(alert_receive_channel, is_default=True, escalation_chain=escalation_chain)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)
    alert_group.raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()
    alert_group.save()

    client = APIClient()
    url = reverse("api-internal:alertgroup-escalation-snapshot", kwargs={"pk": alert_group.public_primary_key})
    expected_result = {
        "escalation_chain": {"name": escalation_chain.name},
        "channel_filter": {"name": "default"},
        "escalation_policies": [
            {
                "step": 13,
                "wait_delay": None,
                "notify_to_users_queue": [{"pk": user.public_primary_key, "username": user.username}],
                "from_time": None,
                "to_time": None,
                "num_alerts_in_window": None,
                "num_minutes_in_window": None,
                "custom_webhook": None,
                "notify_schedule": None,
                "notify_to_group": None,
                "important": False,
            },
            {
                "step": 13,
                "wait_delay": None,
                "notify_to_users_queue": [{"pk": user.public_primary_key, "username": user.username}],
                "from_time": None,
                "to_time": None,
                "num_alerts_in_window": None,
                "num_minutes_in_window": None,
                "custom_webhook": None,
                "notify_schedule": None,
                "notify_to_group": None,
                "important": True,
            },
        ],
    }
    response = client.get(url, **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_result


@pytest.mark.django_db
def test_alert_group_no_escalation_snapshot(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(alert_receive_channel, is_default=True)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)
    client = APIClient()
    url = reverse("api-internal:alertgroup-escalation-snapshot", kwargs={"pk": alert_group.public_primary_key})
    expected_result = {}
    response = client.get(url, **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_result


@pytest.mark.django_db
def test_alert_group_escalation_snapshot_no_policies(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_escalation_chain,
    make_channel_filter,
    make_alert_group,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    escalation_chain = make_escalation_chain(organization)
    channel_filter = make_channel_filter(alert_receive_channel, is_default=True, escalation_chain=escalation_chain)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)
    alert_group.raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()
    alert_group.save()

    client = APIClient()
    url = reverse("api-internal:alertgroup-escalation-snapshot", kwargs={"pk": alert_group.public_primary_key})
    expected_result = {
        "escalation_chain": {"name": escalation_chain.name},
        "channel_filter": {"name": "default"},
        "escalation_policies": [],
    }
    response = client.get(url, **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_result
