import datetime
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.alerts.models import AlertGroup, AlertGroupLogRecord
from apps.api.errors import AlertGroupAPIError
from apps.api.permissions import LegacyAccessControlRole
from apps.base.models import UserNotificationPolicyLogRecord

alert_raw_request_data = {
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
}


@pytest.fixture()
def alert_group_internal_api_setup(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_channel_filter,
    make_resolved_ack_new_silenced_alert_groups,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    default_channel_filter = make_channel_filter(alert_receive_channel, is_default=True)
    alert_groups = make_resolved_ack_new_silenced_alert_groups(
        alert_receive_channel, default_channel_filter, alert_raw_request_data
    )
    return user, token, alert_groups


@pytest.mark.django_db
def test_get_filter_by_integration(
    alert_group_internal_api_setup, make_alert_receive_channel, make_alert_group, make_user_auth_headers
):
    user, token, alert_groups = alert_group_internal_api_setup

    ag = alert_groups[0]
    # channel filter could be None, but the alert group still belongs to the original integration
    ag.channel_filter = None
    ag.save()

    # make an alert group in other integration
    alert_receive_channel = make_alert_receive_channel(user.organization)
    make_alert_group(alert_receive_channel)

    client = APIClient()
    url = reverse("api-internal:alertgroup-list")
    response = client.get(
        url + f"?integration={ag.channel.public_primary_key}",
        format="json",
        **make_user_auth_headers(user, token),
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 4


@pytest.mark.django_db
def test_get_filter_started_at(alert_group_internal_api_setup, make_user_auth_headers):
    user, token, _ = alert_group_internal_api_setup
    client = APIClient()

    url = reverse("api-internal:alertgroup-list")
    response = client.get(
        url + "?started_at=1970-01-01T00:00:00/2099-01-01T23:59:59",
        format="json",
        **make_user_auth_headers(user, token),
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 4


@pytest.mark.django_db
def test_get_filter_resolved_at_alertgroup_empty_result(alert_group_internal_api_setup, make_user_auth_headers):
    client = APIClient()
    user, token, _ = alert_group_internal_api_setup

    url = reverse("api-internal:alertgroup-list")
    response = client.get(
        url + "?resolved_at=1970-01-01T00:00:00/1970-01-01T23:59:59",
        format="json",
        **make_user_auth_headers(user, token),
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 0


@pytest.mark.django_db
def test_get_filter_resolved_at_alertgroup_invalid_format(alert_group_internal_api_setup, make_user_auth_headers):
    client = APIClient()
    user, token, _ = alert_group_internal_api_setup

    url = reverse("api-internal:alertgroup-list")
    response = client.get(
        url + "?resolved_at=invalid_date_format", format="json", **make_user_auth_headers(user, token)
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_get_filter_resolved_at(alert_group_internal_api_setup, make_user_auth_headers):
    client = APIClient()
    user, token, alert_groups = alert_group_internal_api_setup

    url = reverse("api-internal:alertgroup-list")
    response = client.get(
        url + "?resolved_at=1970-01-01T00:00:00/2099-01-01T23:59:59",
        format="json",
        **make_user_auth_headers(user, token),
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1


@pytest.mark.django_db
def test_status_new(alert_group_internal_api_setup, make_user_auth_headers):
    client = APIClient()
    user, token, alert_groups = alert_group_internal_api_setup
    _, _, new_alert_group, _ = alert_groups

    url = reverse("api-internal:alertgroup-list")
    response = client.get(url + "?status=0", format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["pk"] == new_alert_group.public_primary_key


@pytest.mark.django_db
def test_status_ack(alert_group_internal_api_setup, make_user_auth_headers):
    client = APIClient()
    user, token, alert_groups = alert_group_internal_api_setup
    _, ack_alert_group, _, _ = alert_groups

    url = reverse("api-internal:alertgroup-list")
    response = client.get(url + "?status=1", format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["pk"] == ack_alert_group.public_primary_key


@pytest.mark.django_db
def test_status_resolved(alert_group_internal_api_setup, make_user_auth_headers):
    client = APIClient()
    user, token, alert_groups = alert_group_internal_api_setup
    resolved_alert_group, _, _, _ = alert_groups

    url = reverse("api-internal:alertgroup-list")
    response = client.get(url + "?status=2", format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["pk"] == resolved_alert_group.public_primary_key


@pytest.mark.django_db
def test_status_silenced(alert_group_internal_api_setup, make_user_auth_headers):
    client = APIClient()
    user, token, alert_groups = alert_group_internal_api_setup
    _, _, _, silenced_alert_group = alert_groups

    url = reverse("api-internal:alertgroup-list")
    response = client.get(url + "?status=3", format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["pk"] == silenced_alert_group.public_primary_key


@pytest.mark.django_db
def test_all_statuses(alert_group_internal_api_setup, make_user_auth_headers):
    client = APIClient()
    user, token, alert_groups = alert_group_internal_api_setup
    resolved_alert_group, _, _, _ = alert_groups

    url = reverse("api-internal:alertgroup-list")
    response = client.get(
        url + "?status=0&status=1&&status=2&status=3", format="json", **make_user_auth_headers(user, token)
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 4


@pytest.mark.django_db
def test_get_filter_resolved_by(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_alert,
    make_resolved_ack_new_silenced_alert_groups,
    make_user_auth_headers,
):
    client = APIClient()

    organization, first_user, token = make_organization_and_user_with_plugin_token()
    second_user = make_user_for_organization(organization)

    alert_receive_channel = make_alert_receive_channel(organization)
    default_channel_filter = make_channel_filter(alert_receive_channel, is_default=True)

    resolved_alert_group = make_alert_group(
        alert_receive_channel,
        channel_filter=default_channel_filter,
        acknowledged_at=timezone.now() + datetime.timedelta(hours=1),
        resolved_at=timezone.now() + datetime.timedelta(hours=2),
        resolved=True,
        acknowledged=True,
        resolved_by_user=first_user,
        acknowledged_by_user=second_user,
    )
    make_alert(alert_group=resolved_alert_group, raw_request_data=alert_raw_request_data)

    url = reverse("api-internal:alertgroup-list")

    first_response = client.get(
        url + f"?resolved_by={first_user.public_primary_key}",
        format="json",
        **make_user_auth_headers(first_user, token),
    )
    assert first_response.status_code == status.HTTP_200_OK
    assert len(first_response.data["results"]) == 1

    second_response = client.get(
        url + f"?resolved_by={second_user.public_primary_key}",
        format="json",
        **make_user_auth_headers(first_user, token),
    )
    assert second_response.status_code == status.HTTP_200_OK
    assert len(second_response.data["results"]) == 0


@pytest.mark.django_db
def test_get_filter_resolved_by_multiple_values(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_alert,
    make_resolved_ack_new_silenced_alert_groups,
    make_user_auth_headers,
):
    client = APIClient()

    organization, first_user, token = make_organization_and_user_with_plugin_token()
    second_user = make_user_for_organization(organization)
    third_user = make_user_for_organization(organization)

    alert_receive_channel = make_alert_receive_channel(organization)
    default_channel_filter = make_channel_filter(alert_receive_channel, is_default=True)

    def make_resolved_by_user_alert_group(user):
        resolved_alert_group = make_alert_group(
            alert_receive_channel,
            channel_filter=default_channel_filter,
            acknowledged_at=timezone.now() + datetime.timedelta(hours=1),
            resolved_at=timezone.now() + datetime.timedelta(hours=2),
            resolved=True,
            acknowledged=True,
            resolved_by_user=user,
            acknowledged_by_user=user,
        )
        make_alert(alert_group=resolved_alert_group, raw_request_data=alert_raw_request_data)

    make_resolved_by_user_alert_group(first_user)
    make_resolved_by_user_alert_group(second_user)
    make_resolved_by_user_alert_group(third_user)

    url = reverse("api-internal:alertgroup-list")

    first_response = client.get(
        url + f"?resolved_by={first_user.public_primary_key}&" f"resolved_by={second_user.public_primary_key}",
        format="json",
        **make_user_auth_headers(first_user, token),
    )
    assert first_response.status_code == status.HTTP_200_OK
    assert len(first_response.data["results"]) == 2


@pytest.mark.django_db
def test_get_filter_acknowledged_by(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_alert,
    make_resolved_ack_new_silenced_alert_groups,
    make_user_auth_headers,
):
    client = APIClient()

    organization, first_user, token = make_organization_and_user_with_plugin_token()
    second_user = make_user_for_organization(organization)

    alert_receive_channel = make_alert_receive_channel(organization)
    default_channel_filter = make_channel_filter(alert_receive_channel, is_default=True)

    acknowledged_alert_group = make_alert_group(
        alert_receive_channel,
        channel_filter=default_channel_filter,
        acknowledged_at=timezone.now() + datetime.timedelta(hours=1),
        resolved_at=timezone.now() + datetime.timedelta(hours=2),
        acknowledged=True,
        acknowledged_by_user=first_user,
    )
    make_alert(alert_group=acknowledged_alert_group, raw_request_data=alert_raw_request_data)

    url = reverse("api-internal:alertgroup-list")

    first_response = client.get(
        url + f"?acknowledged_by={first_user.public_primary_key}",
        format="json",
        **make_user_auth_headers(first_user, token),
    )
    assert first_response.status_code == status.HTTP_200_OK
    assert len(first_response.data["results"]) == 1

    second_response = client.get(
        url + f"?acknowledged_by={second_user.public_primary_key}",
        format="json",
        **make_user_auth_headers(first_user, token),
    )
    assert second_response.status_code == status.HTTP_200_OK
    assert len(second_response.data["results"]) == 0


@pytest.mark.django_db
def test_get_filter_acknowledged_by_multiple_values(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_alert,
    make_resolved_ack_new_silenced_alert_groups,
    make_user_auth_headers,
):
    client = APIClient()

    organization, first_user, token = make_organization_and_user_with_plugin_token()
    second_user = make_user_for_organization(organization)
    third_user = make_user_for_organization(organization)

    alert_receive_channel = make_alert_receive_channel(organization)
    default_channel_filter = make_channel_filter(alert_receive_channel, is_default=True)

    def make_acknowledged_by_user_alert_group(user):
        acknowledged_alert_group = make_alert_group(
            alert_receive_channel,
            channel_filter=default_channel_filter,
            acknowledged_at=timezone.now() + datetime.timedelta(hours=1),
            resolved_at=timezone.now() + datetime.timedelta(hours=2),
            acknowledged=True,
            acknowledged_by_user=user,
        )
        make_alert(alert_group=acknowledged_alert_group, raw_request_data=alert_raw_request_data)

    make_acknowledged_by_user_alert_group(first_user)
    make_acknowledged_by_user_alert_group(second_user)
    make_acknowledged_by_user_alert_group(third_user)

    url = reverse("api-internal:alertgroup-list")

    first_response = client.get(
        url + f"?acknowledged_by={first_user.public_primary_key}" f"&acknowledged_by={second_user.public_primary_key}",
        format="json",
        **make_user_auth_headers(first_user, token),
    )
    assert first_response.status_code == status.HTTP_200_OK
    assert len(first_response.data["results"]) == 2


@pytest.mark.django_db
def test_get_filter_silenced_by(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_alert,
    make_resolved_ack_new_silenced_alert_groups,
    make_user_auth_headers,
):
    client = APIClient()

    organization, first_user, token = make_organization_and_user_with_plugin_token()
    second_user = make_user_for_organization(organization)

    alert_receive_channel = make_alert_receive_channel(organization)
    default_channel_filter = make_channel_filter(alert_receive_channel, is_default=True)

    silenced_alert_group = make_alert_group(
        alert_receive_channel,
        channel_filter=default_channel_filter,
        silenced_at=timezone.now() + datetime.timedelta(hours=1),
        silenced=True,
        silenced_by_user=first_user,
    )
    make_alert(alert_group=silenced_alert_group, raw_request_data=alert_raw_request_data)

    url = reverse("api-internal:alertgroup-list")

    first_response = client.get(
        url + f"?silenced_by={first_user.public_primary_key}",
        format="json",
        **make_user_auth_headers(first_user, token),
    )
    assert first_response.status_code == status.HTTP_200_OK
    assert len(first_response.data["results"]) == 1

    second_response = client.get(
        url + f"?silenced_by={second_user.public_primary_key}",
        format="json",
        **make_user_auth_headers(first_user, token),
    )
    assert second_response.status_code == status.HTTP_200_OK
    assert len(second_response.data["results"]) == 0


@pytest.mark.django_db
def test_get_filter_silenced_by_multiple_values(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_alert,
    make_resolved_ack_new_silenced_alert_groups,
    make_user_auth_headers,
):
    client = APIClient()

    organization, first_user, token = make_organization_and_user_with_plugin_token()
    second_user = make_user_for_organization(organization)
    third_user = make_user_for_organization(organization)

    alert_receive_channel = make_alert_receive_channel(organization)
    default_channel_filter = make_channel_filter(alert_receive_channel, is_default=True)

    def make_silenced_by_user_alert_group(user):
        acknowledged_alert_group = make_alert_group(
            alert_receive_channel,
            channel_filter=default_channel_filter,
            silenced_at=timezone.now() + datetime.timedelta(hours=1),
            silenced=True,
            silenced_by_user=user,
        )
        make_alert(alert_group=acknowledged_alert_group, raw_request_data=alert_raw_request_data)

    make_silenced_by_user_alert_group(first_user)
    make_silenced_by_user_alert_group(second_user)
    make_silenced_by_user_alert_group(third_user)

    url = reverse("api-internal:alertgroup-list")

    first_response = client.get(
        url + f"?silenced_by={first_user.public_primary_key}&silenced_by={second_user.public_primary_key}",
        format="json",
        **make_user_auth_headers(first_user, token),
    )
    assert first_response.status_code == status.HTTP_200_OK
    assert len(first_response.data["results"]) == 2


@pytest.mark.django_db
def test_get_filter_invitees_are(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_alert,
    make_user_auth_headers,
):
    client = APIClient()

    organization, first_user, token = make_organization_and_user_with_plugin_token()
    second_user = make_user_for_organization(organization)

    alert_receive_channel = make_alert_receive_channel(organization)
    default_channel_filter = make_channel_filter(alert_receive_channel, is_default=True)

    alert_group = make_alert_group(
        alert_receive_channel,
        channel_filter=default_channel_filter,
    )
    make_alert(alert_group=alert_group, raw_request_data={})
    alert_group.log_records.create(
        type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED,
        author=first_user,
    )

    url = reverse("api-internal:alertgroup-list")

    first_response = client.get(
        url + f"?invitees_are={first_user.public_primary_key}",
        format="json",
        **make_user_auth_headers(first_user, token),
    )
    assert first_response.status_code == status.HTTP_200_OK
    assert len(first_response.data["results"]) == 1

    second_response = client.get(
        url + f"?invitees_are={second_user.public_primary_key}",
        format="json",
        **make_user_auth_headers(first_user, token),
    )
    assert second_response.status_code == status.HTTP_200_OK
    assert len(second_response.data["results"]) == 0


@pytest.mark.django_db
def test_get_filter_invitees_are_multiple_values(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_alert,
    make_user_auth_headers,
):
    client = APIClient()

    organization, first_user, token = make_organization_and_user_with_plugin_token()
    second_user = make_user_for_organization(organization)
    third_user = make_user_for_organization(organization)

    alert_receive_channel = make_alert_receive_channel(organization)
    default_channel_filter = make_channel_filter(alert_receive_channel, is_default=True)

    def make_alert_group_with_invitee(user):
        alert_group = make_alert_group(
            alert_receive_channel,
            channel_filter=default_channel_filter,
        )
        make_alert(alert_group=alert_group, raw_request_data={})

        alert_group.log_records.create(
            type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED,
            author=user,
        )

    make_alert_group_with_invitee(first_user)
    make_alert_group_with_invitee(second_user)
    make_alert_group_with_invitee(third_user)

    url = reverse("api-internal:alertgroup-list")

    first_response = client.get(
        url + f"?invitees_are={first_user.public_primary_key}" f"&invitees_are={second_user.public_primary_key}",
        format="json",
        **make_user_auth_headers(first_user, token),
    )
    assert first_response.status_code == status.HTTP_200_OK
    assert len(first_response.data["results"]) == 2


@pytest.mark.django_db
def test_get_filter_invitees_are_ag_with_multiple_logs(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_alert,
    make_user_auth_headers,
):
    client = APIClient()

    organization, first_user, token = make_organization_and_user_with_plugin_token()
    second_user = make_user_for_organization(organization)

    alert_receive_channel = make_alert_receive_channel(organization)
    default_channel_filter = make_channel_filter(alert_receive_channel, is_default=True)

    alert_group = make_alert_group(
        alert_receive_channel,
        channel_filter=default_channel_filter,
    )
    make_alert(alert_group=alert_group, raw_request_data={})

    alert_group.log_records.create(
        type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED,
        author=first_user,
    )

    alert_group.log_records.create(
        type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED,
        author=second_user,
    )

    url = reverse("api-internal:alertgroup-list")

    first_response = client.get(
        url + f"?invitees_are={first_user.public_primary_key}" f"&invitees_are={second_user.public_primary_key}",
        format="json",
        **make_user_auth_headers(first_user, token),
    )
    assert first_response.status_code == status.HTTP_200_OK
    assert len(first_response.data["results"]) == 1


@pytest.mark.django_db
def test_get_filter_mine(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_alert,
    make_user_auth_headers,
):
    client = APIClient()

    organization, first_user, token = make_organization_and_user_with_plugin_token()

    alert_receive_channel = make_alert_receive_channel(organization)
    default_channel_filter = make_channel_filter(alert_receive_channel, is_default=True)

    acknowledged_alert_group = make_alert_group(
        alert_receive_channel,
        channel_filter=default_channel_filter,
        acknowledged_at=timezone.now() + datetime.timedelta(hours=1),
        resolved_at=timezone.now() + datetime.timedelta(hours=2),
        acknowledged=True,
        acknowledged_by_user=first_user,
    )
    make_alert(alert_group=acknowledged_alert_group, raw_request_data=alert_raw_request_data)

    # other alert group
    make_alert_group(
        alert_receive_channel,
        channel_filter=default_channel_filter,
    )
    make_alert(alert_group=acknowledged_alert_group, raw_request_data=alert_raw_request_data)

    url = reverse("api-internal:alertgroup-list")

    first_response = client.get(
        url + "?mine=true",
        format="json",
        **make_user_auth_headers(first_user, token),
    )
    assert first_response.status_code == status.HTTP_200_OK
    assert len(first_response.data["results"]) == 1

    second_response = client.get(
        url + "?mine=false",
        format="json",
        **make_user_auth_headers(first_user, token),
    )
    assert second_response.status_code == status.HTTP_200_OK
    assert len(second_response.data["results"]) == 2


@pytest.mark.django_db
def test_get_filter_involved_users(
    make_organization_and_user_with_plugin_token,
    make_user_for_organization,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_alert,
    make_user_auth_headers,
):
    client = APIClient()

    organization, first_user, token = make_organization_and_user_with_plugin_token()
    second_user = make_user_for_organization(organization)

    alert_receive_channel = make_alert_receive_channel(organization)
    default_channel_filter = make_channel_filter(alert_receive_channel, is_default=True)

    acknowledged_alert_group = make_alert_group(
        alert_receive_channel,
        channel_filter=default_channel_filter,
        acknowledged_at=timezone.now() + datetime.timedelta(hours=1),
        resolved_at=timezone.now() + datetime.timedelta(hours=2),
        acknowledged=True,
        acknowledged_by_user=first_user,
    )
    make_alert(alert_group=acknowledged_alert_group, raw_request_data=alert_raw_request_data)

    # other alert group
    other_alert_group = make_alert_group(
        alert_receive_channel,
        channel_filter=default_channel_filter,
    )
    make_alert(alert_group=acknowledged_alert_group, raw_request_data=alert_raw_request_data)
    # second user was notified
    other_alert_group.personal_log_records.create(
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
        author=second_user,
    )

    url = reverse("api-internal:alertgroup-list")

    first_response = client.get(
        url + f"?acknowledged_by={first_user.public_primary_key}",
        format="json",
        **make_user_auth_headers(first_user, token),
    )
    assert first_response.status_code == status.HTTP_200_OK
    assert len(first_response.data["results"]) == 1

    second_response = client.get(
        url
        + f"?involved_users_are={first_user.public_primary_key}&involved_users_are={second_user.public_primary_key}",
        format="json",
        **make_user_auth_headers(first_user, token),
    )
    assert second_response.status_code == status.HTTP_200_OK
    assert len(second_response.data["results"]) == 2


@pytest.mark.django_db
def test_get_filter_with_resolution_note(
    alert_group_internal_api_setup,
    make_resolution_note,
    make_user_auth_headers,
):
    user, token, alert_groups = alert_group_internal_api_setup
    res_alert_group, ack_alert_group, _, _ = alert_groups
    client = APIClient()

    url = reverse("api-internal:alertgroup-list")

    # there are no alert groups with resolution_notes
    response = client.get(url + "?with_resolution_note=true", format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 0

    response = client.get(url + "?with_resolution_note=false", format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 4

    # add resolution_notes to two of four alert groups
    make_resolution_note(res_alert_group)
    make_resolution_note(ack_alert_group)

    response = client.get(url + "?with_resolution_note=true", format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 2

    response = client.get(url + "?with_resolution_note=false", format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 2


@pytest.mark.django_db
def test_get_filter_with_resolution_note_after_delete_resolution_note(
    alert_group_internal_api_setup,
    make_resolution_note,
    make_user_auth_headers,
):
    user, token, alert_groups = alert_group_internal_api_setup
    res_alert_group, ack_alert_group, _, _ = alert_groups
    client = APIClient()

    url = reverse("api-internal:alertgroup-list")

    # add resolution note to two alert group
    resolution_note_res_alert_group = make_resolution_note(res_alert_group)
    make_resolution_note(ack_alert_group)

    # delete resolution note message using soft delete
    resolution_note_res_alert_group.delete()
    resolution_note_res_alert_group.refresh_from_db()
    assert resolution_note_res_alert_group.deleted_at is not None

    response = client.get(url + "?with_resolution_note=true", format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1


@pytest.mark.django_db
def test_get_filter_escalation_chain(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_channel_filter,
    make_escalation_chain,
    make_alert_group,
    make_alert,
    make_user_auth_headers,
):
    client = APIClient()
    organization, user, token = make_organization_and_user_with_plugin_token()

    alert_receive_channel = make_alert_receive_channel(organization)

    escalation_chain_1 = make_escalation_chain(organization=organization)
    escalation_chain_2 = make_escalation_chain(organization=organization)

    channel_filter_1 = make_channel_filter(alert_receive_channel, escalation_chain=escalation_chain_1, is_default=True)
    channel_filter_2 = make_channel_filter(alert_receive_channel, escalation_chain=escalation_chain_2, is_default=False)

    alert_group_1 = make_alert_group(alert_receive_channel, channel_filter=channel_filter_1)
    make_alert(alert_group=alert_group_1, raw_request_data=alert_raw_request_data)

    alert_group_2 = make_alert_group(alert_receive_channel, channel_filter=channel_filter_2)
    make_alert(alert_group=alert_group_2, raw_request_data=alert_raw_request_data)

    url = reverse("api-internal:alertgroup-list")

    # check when a single escalation chain is passed
    response = client.get(
        url + f"?escalation_chain={escalation_chain_1.public_primary_key}", **make_user_auth_headers(user, token)
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["pk"] == alert_group_1.public_primary_key

    # check when multiple escalation chains are passed
    response = client.get(
        url
        + f"?escalation_chain={escalation_chain_1.public_primary_key}&escalation_chain={escalation_chain_2.public_primary_key}",
        **make_user_auth_headers(user, token),
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 2


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_alert_group_acknowledge_permissions(
    alert_group_internal_api_setup,
    make_user_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, token, alert_groups = alert_group_internal_api_setup
    _, _, new_alert_group, _ = alert_groups
    organization = new_alert_group.channel.organization
    user = make_user_for_organization(organization, role)

    client = APIClient()

    url = reverse("api-internal:alertgroup-acknowledge", kwargs={"pk": new_alert_group.public_primary_key})

    with patch(
        "apps.api.views.alert_group.AlertGroupView.acknowledge",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.post(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_alert_group_unacknowledge_permissions(
    alert_group_internal_api_setup,
    make_user_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, token, alert_groups = alert_group_internal_api_setup
    _, _, new_alert_group, _ = alert_groups
    organization = new_alert_group.channel.organization
    user = make_user_for_organization(organization, role)

    client = APIClient()
    url = reverse("api-internal:alertgroup-unacknowledge", kwargs={"pk": new_alert_group.public_primary_key})

    with patch(
        "apps.api.views.alert_group.AlertGroupView.unacknowledge",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.post(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_alert_group_resolve_permissions(
    alert_group_internal_api_setup,
    make_user_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, token, alert_groups = alert_group_internal_api_setup
    _, _, new_alert_group, _ = alert_groups
    organization = new_alert_group.channel.organization
    user = make_user_for_organization(organization, role)

    client = APIClient()
    url = reverse("api-internal:alertgroup-resolve", kwargs={"pk": new_alert_group.public_primary_key})

    with patch(
        "apps.api.views.alert_group.AlertGroupView.resolve",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.post(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_alert_group_unresolve_permissions(
    alert_group_internal_api_setup,
    make_user_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, token, alert_groups = alert_group_internal_api_setup
    _, _, new_alert_group, _ = alert_groups
    organization = new_alert_group.channel.organization
    user = make_user_for_organization(organization, role)

    client = APIClient()
    url = reverse("api-internal:alertgroup-unresolve", kwargs={"pk": new_alert_group.public_primary_key})

    with patch(
        "apps.api.views.alert_group.AlertGroupView.unresolve",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.post(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_alert_group_silence_permissions(
    alert_group_internal_api_setup,
    make_user_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, token, alert_groups = alert_group_internal_api_setup
    _, _, new_alert_group, _ = alert_groups
    organization = new_alert_group.channel.organization
    user = make_user_for_organization(organization, role)

    client = APIClient()
    url = reverse("api-internal:alertgroup-silence", kwargs={"pk": new_alert_group.public_primary_key})

    with patch(
        "apps.api.views.alert_group.AlertGroupView.silence",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.post(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_alert_group_unsilence_permissions(
    alert_group_internal_api_setup,
    make_user_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, token, alert_groups = alert_group_internal_api_setup
    _, _, new_alert_group, _ = alert_groups
    organization = new_alert_group.channel.organization
    user = make_user_for_organization(organization, role)

    client = APIClient()
    url = reverse("api-internal:alertgroup-unsilence", kwargs={"pk": new_alert_group.public_primary_key})

    with patch(
        "apps.api.views.alert_group.AlertGroupView.unsilence",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.post(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_alert_group_attach_permissions(
    alert_group_internal_api_setup,
    make_user_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, token, alert_groups = alert_group_internal_api_setup
    _, _, new_alert_group, _ = alert_groups
    organization = new_alert_group.channel.organization
    user = make_user_for_organization(organization, role)

    client = APIClient()
    url = reverse("api-internal:alertgroup-attach", kwargs={"pk": new_alert_group.public_primary_key})

    with patch(
        "apps.api.views.alert_group.AlertGroupView.attach",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.post(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_alert_group_unattach_permissions(
    alert_group_internal_api_setup,
    make_user_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, token, alert_groups = alert_group_internal_api_setup
    _, _, new_alert_group, _ = alert_groups
    organization = new_alert_group.channel.organization
    user = make_user_for_organization(organization, role)

    client = APIClient()
    url = reverse("api-internal:alertgroup-unattach", kwargs={"pk": new_alert_group.public_primary_key})

    with patch(
        "apps.api.views.alert_group.AlertGroupView.unattach",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.post(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
    ],
)
def test_alert_group_list_permissions(
    alert_group_internal_api_setup,
    make_user_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, token, alert_groups = alert_group_internal_api_setup
    _, _, new_alert_group, _ = alert_groups
    organization = new_alert_group.channel.organization
    user = make_user_for_organization(organization, role)

    client = APIClient()
    url = reverse("api-internal:alertgroup-list")

    with patch(
        "apps.api.views.alert_group.AlertGroupView.list",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
    ],
)
def test_alert_group_stats_permissions(
    alert_group_internal_api_setup,
    make_user_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, token, alert_groups = alert_group_internal_api_setup
    _, _, new_alert_group, _ = alert_groups
    organization = new_alert_group.channel.organization
    user = make_user_for_organization(organization, role)

    client = APIClient()
    url = reverse("api-internal:alertgroup-stats")

    with patch(
        "apps.api.views.alert_group.AlertGroupView.stats",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_alert_group_bulk_action_permissions(
    alert_group_internal_api_setup,
    make_user_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, token, alert_groups = alert_group_internal_api_setup
    _, _, new_alert_group, _ = alert_groups
    organization = new_alert_group.channel.organization
    user = make_user_for_organization(organization, role)

    client = APIClient()
    url = reverse("api-internal:alertgroup-bulk-action")

    with patch(
        "apps.api.views.alert_group.AlertGroupView.bulk_action", return_value=Response(status=status.HTTP_200_OK)
    ):
        response = client.post(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
    ],
)
def test_alert_group_filters_permissions(
    alert_group_internal_api_setup,
    make_user_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, token, alert_groups = alert_group_internal_api_setup
    _, _, new_alert_group, _ = alert_groups
    organization = new_alert_group.channel.organization
    user = make_user_for_organization(organization, role)

    client = APIClient()
    url = reverse("api-internal:alertgroup-filters")

    with patch(
        "apps.api.views.alert_group.AlertGroupView.filters",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
    ],
)
def test_alert_group_detail_permissions(
    alert_group_internal_api_setup,
    make_user_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, token, alert_groups = alert_group_internal_api_setup
    _, _, new_alert_group, _ = alert_groups
    organization = new_alert_group.channel.organization
    user = make_user_for_organization(organization, role)

    client = APIClient()
    url = reverse("api-internal:alertgroup-detail", kwargs={"pk": new_alert_group.public_primary_key})

    with patch(
        "apps.api.views.alert_group.AlertGroupView.retrieve",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == expected_status


@pytest.mark.django_db
def test_silence(alert_group_internal_api_setup, make_user_auth_headers):
    client = APIClient()
    user, token, alert_groups = alert_group_internal_api_setup
    _, _, new_alert_group, _ = alert_groups
    url = reverse("api-internal:alertgroup-silence", kwargs={"pk": new_alert_group.public_primary_key})

    silence_delay = timezone.timedelta(seconds=60)
    response = client.post(
        url, data={"delay": silence_delay.seconds}, format="json", **make_user_auth_headers(user, token)
    )

    assert response.status_code == status.HTTP_200_OK

    new_alert_group.refresh_from_db()
    assert new_alert_group.silenced_until is not None

    assert new_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_SILENCE, author=user, silence_delay=silence_delay
    ).exists()


@pytest.mark.django_db
def test_unsilence(
    alert_group_internal_api_setup,
    make_user_auth_headers,
):
    client = APIClient()
    user, token, alert_groups = alert_group_internal_api_setup
    _, _, new_alert_group, _ = alert_groups

    silence_url = reverse("api-internal:alertgroup-silence", kwargs={"pk": new_alert_group.public_primary_key})
    unsilence_url = reverse("api-internal:alertgroup-unsilence", kwargs={"pk": new_alert_group.public_primary_key})

    # silence alert group
    silence_delay = timezone.timedelta(seconds=10000)
    client.post(
        silence_url, data={"delay": silence_delay.seconds}, format="json", **make_user_auth_headers(user, token)
    )

    # unsnooze alert group
    response = client.post(unsilence_url, **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK

    new_alert_group.refresh_from_db()
    assert new_alert_group.silenced_until is None

    assert new_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_UN_SILENCE,
        author=user,
    ).exists()


@pytest.mark.django_db
def test_unpage_user(
    alert_group_internal_api_setup,
    make_user,
    make_user_auth_headers,
):
    client = APIClient()
    user, token, alert_groups = alert_group_internal_api_setup
    user_to_unpage = make_user(organization=user.organization)
    _, _, new_alert_group, _ = alert_groups

    url = reverse("api-internal:alertgroup-unpage-user", kwargs={"pk": new_alert_group.public_primary_key})
    response = client.post(
        url, data={"user_id": user_to_unpage.public_primary_key}, **make_user_auth_headers(user, token)
    )

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_invalid_bulk_action(
    make_user_auth_headers,
    alert_group_internal_api_setup,
):
    client = APIClient()
    user, token, alert_groups = alert_group_internal_api_setup
    _, _, new_alert_group, _ = alert_groups

    url = reverse("api-internal:alertgroup-bulk-action")

    response = client.post(
        url,
        data={
            "alert_group_pks": [alert_group.public_primary_key for alert_group in alert_groups],
            "action": "invalid_action",
        },
        format="json",
        **make_user_auth_headers(user, token),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@patch("apps.alerts.tasks.send_alert_group_signal.send_alert_group_signal.apply_async", return_value=None)
@patch("apps.alerts.tasks.send_update_log_report_signal.send_update_log_report_signal.apply_async", return_value=None)
@patch("apps.alerts.models.AlertGroup.start_escalation_if_needed", return_value=None)
@pytest.mark.django_db
def test_bulk_action_restart(
    mocked_alert_group_signal_task,
    mocked_log_report_signal_task,
    mocked_start_escalate_alert,
    make_user_auth_headers,
    alert_group_internal_api_setup,
):
    client = APIClient()
    user, token, alert_groups = alert_group_internal_api_setup
    resolved_alert_group, acked_alert_group, new_alert_group, silenced_alert_group = alert_groups

    url = reverse("api-internal:alertgroup-bulk-action")

    assert not resolved_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_UN_RESOLVED,
        author=user,
    ).exists()

    assert not acked_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_UN_ACK,
        author=user,
    ).exists()

    assert not silenced_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_UN_SILENCE,
        author=user,
    ).exists()

    # restart alert groups
    response = client.post(
        url,
        data={
            "alert_group_pks": [alert_group.public_primary_key for alert_group in alert_groups],
            "action": AlertGroup.RESTART,
        },
        format="json",
        **make_user_auth_headers(user, token),
    )

    assert response.status_code == status.HTTP_200_OK

    assert resolved_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_UN_RESOLVED,
        author=user,
    ).exists()

    assert acked_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_UN_ACK,
        author=user,
    ).exists()

    assert silenced_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_UN_SILENCE,
        author=user,
    ).exists()

    assert mocked_alert_group_signal_task.called
    assert mocked_log_report_signal_task.called
    assert mocked_start_escalate_alert.called


@patch("apps.alerts.tasks.send_alert_group_signal.send_alert_group_signal.apply_async", return_value=None)
@patch("apps.alerts.tasks.send_update_log_report_signal.send_update_log_report_signal.apply_async", return_value=None)
@pytest.mark.django_db
def test_bulk_action_acknowledge(
    mocked_alert_group_signal_task,
    mocked_log_report_signal_task,
    make_user_auth_headers,
    alert_group_internal_api_setup,
):
    client = APIClient()
    user, token, alert_groups = alert_group_internal_api_setup
    resolved_alert_group, acked_alert_group, new_alert_group, _ = alert_groups

    url = reverse("api-internal:alertgroup-bulk-action")

    assert not new_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_UN_RESOLVED,
        author=user,
    ).exists()

    # acknowledge alert groups
    response = client.post(
        url,
        data={
            "alert_group_pks": [alert_group.public_primary_key for alert_group in alert_groups],
            "action": AlertGroup.ACKNOWLEDGE,
        },
        format="json",
        **make_user_auth_headers(user, token),
    )

    assert response.status_code == status.HTTP_200_OK

    assert new_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_ACK,
        author=user,
    ).exists()

    assert resolved_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_UN_RESOLVED,
        author=user,
    ).exists()

    assert resolved_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_ACK,
        author=user,
    ).exists()

    assert not acked_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_ACK,
        author=user,
    ).exists()

    assert mocked_alert_group_signal_task.called
    assert mocked_log_report_signal_task.called


@patch("apps.alerts.tasks.send_alert_group_signal.send_alert_group_signal.apply_async", return_value=None)
@patch("apps.alerts.tasks.send_update_log_report_signal.send_update_log_report_signal.apply_async", return_value=None)
@pytest.mark.django_db
def test_bulk_action_resolve(
    mocked_alert_group_signal_task,
    mocked_log_report_signal_task,
    make_user_auth_headers,
    alert_group_internal_api_setup,
):
    client = APIClient()
    user, token, alert_groups = alert_group_internal_api_setup
    resolved_alert_group, acked_alert_group, new_alert_group, _ = alert_groups

    url = reverse("api-internal:alertgroup-bulk-action")

    assert not new_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_RESOLVED,
        author=user,
    ).exists()

    # resolve alert groups
    response = client.post(
        url,
        data={
            "alert_group_pks": [alert_group.public_primary_key for alert_group in alert_groups],
            "action": AlertGroup.RESOLVE,
        },
        format="json",
        **make_user_auth_headers(user, token),
    )

    assert response.status_code == status.HTTP_200_OK

    assert new_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_RESOLVED,
        author=user,
    ).exists()

    assert acked_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_RESOLVED,
        author=user,
    ).exists()

    assert not resolved_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_RESOLVED,
        author=user,
    ).exists()

    assert mocked_alert_group_signal_task.called
    assert mocked_log_report_signal_task.called


@patch("apps.alerts.tasks.send_alert_group_signal.send_alert_group_signal.apply_async", return_value=None)
@patch("apps.alerts.tasks.send_update_log_report_signal.send_update_log_report_signal.apply_async", return_value=None)
@patch("apps.alerts.models.AlertGroup.start_unsilence_task", return_value=None)
@pytest.mark.django_db
def test_bulk_action_silence(
    mocked_alert_group_signal_task,
    mocked_log_report_signal_task,
    mocked_start_unsilence_task,
    make_user_auth_headers,
    alert_group_internal_api_setup,
):
    client = APIClient()
    user, token, alert_groups = alert_group_internal_api_setup
    resolved_alert_group, acked_alert_group, new_alert_group, silenced_alert_groups = alert_groups

    url = reverse("api-internal:alertgroup-bulk-action")

    assert not new_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_SILENCE,
        author=user,
    ).exists()

    # silence alert groups
    response = client.post(
        url,
        data={
            "alert_group_pks": [alert_group.public_primary_key for alert_group in alert_groups],
            "action": AlertGroup.SILENCE,
            "delay": 180,
        },
        format="json",
        **make_user_auth_headers(user, token),
    )

    assert response.status_code == status.HTTP_200_OK

    assert new_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_SILENCE,
        author=user,
    ).exists()

    new_alert_group.refresh_from_db()
    assert new_alert_group.silenced

    assert acked_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_UN_ACK,
        author=user,
    ).exists()

    assert acked_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_SILENCE,
        author=user,
    ).exists()

    assert resolved_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_UN_RESOLVED,
        author=user,
    ).exists()

    assert resolved_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_SILENCE,
        author=user,
    ).exists()

    assert silenced_alert_groups.log_records.filter(
        type=AlertGroupLogRecord.TYPE_UN_SILENCE,
        author=user,
    ).exists()

    assert silenced_alert_groups.log_records.filter(
        type=AlertGroupLogRecord.TYPE_SILENCE,
        author=user,
    ).exists()

    assert mocked_alert_group_signal_task.called
    assert mocked_log_report_signal_task.called
    assert mocked_start_unsilence_task.called


@pytest.mark.django_db
def test_alert_group_status_field(
    make_user_auth_headers,
    alert_group_internal_api_setup,
):
    client = APIClient()

    user, token, alert_groups = alert_group_internal_api_setup
    resolved_alert_group, acked_alert_group, new_alert_group, silenced_alert_group = alert_groups

    url = reverse("api-internal:alertgroup-detail", kwargs={"pk": new_alert_group.public_primary_key})
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.json()["status"] == AlertGroup.NEW

    url = reverse("api-internal:alertgroup-detail", kwargs={"pk": acked_alert_group.public_primary_key})
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.json()["status"] == AlertGroup.ACKNOWLEDGED

    url = reverse("api-internal:alertgroup-detail", kwargs={"pk": resolved_alert_group.public_primary_key})
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.json()["status"] == AlertGroup.RESOLVED

    url = reverse("api-internal:alertgroup-detail", kwargs={"pk": silenced_alert_group.public_primary_key})
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.json()["status"] == AlertGroup.SILENCED


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_alert_group_preview_template_permissions(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_user_auth_headers,
    role,
    expected_status,
    make_alert_group,
    make_alert,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role=role)
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)

    client = APIClient()
    url = reverse("api-internal:alertgroup-preview-template", kwargs={"pk": alert_group.public_primary_key})

    with patch(
        "apps.api.views.alert_group.AlertGroupView.preview_template",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.post(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
def test_alert_group_preview_body_non_existent_template_var(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_user_auth_headers,
    make_alert_group,
    make_alert,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    client = APIClient()
    url = reverse("api-internal:alertgroup-preview-template", kwargs={"pk": alert_group.public_primary_key})

    data = {"template_name": "testonly_title_template", "template_body": "foobar: {{ foobar.does_not_exist }}"}
    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))

    # Return errors as preview body instead of None
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["preview"] == "Template Warning: &#x27;foobar&#x27; is undefined"


@pytest.mark.django_db
def test_alert_group_preview_body_invalid_template_syntax(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_user_auth_headers,
    make_alert_group,
    make_alert,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    client = APIClient()
    url = reverse("api-internal:alertgroup-preview-template", kwargs={"pk": alert_group.public_primary_key})

    data = {"template_name": "testonly_title_template", "template_body": "{{'' if foo is None else foo}}"}
    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))

    # Errors now returned preview content
    assert response.status_code == status.HTTP_200_OK
    assert response.data["preview"] == "Template Error: No test named &#x27;None&#x27; found."


@pytest.mark.django_db
def test_grouped_alerts(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    # create 101 alerts and check that only 100 are returned
    for i in range(101):
        make_alert(
            alert_group=alert_group,
            created_at=timezone.datetime.min + timezone.timedelta(minutes=i),
            raw_request_data=alert_receive_channel.config.example_payload,
        )

    client = APIClient()
    url = reverse("api-internal:alertgroup-detail", kwargs={"pk": alert_group.public_primary_key})

    response = client.get(url, **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["alerts"]) == 100

    first_alert_created_at = response.json()["alerts"][0]["created_at"]
    last_alert_created_at = response.json()["alerts"][-1]["created_at"]

    first_alert_created_at = timezone.datetime.strptime(first_alert_created_at, "%Y-%m-%dT%H:%M:%S.%fZ")
    last_alert_created_at = timezone.datetime.strptime(last_alert_created_at, "%Y-%m-%dT%H:%M:%S.%fZ")

    assert first_alert_created_at > last_alert_created_at


@pytest.mark.django_db
def test_alert_group_paged_users(
    make_user_for_organization,
    make_user_auth_headers,
    alert_group_internal_api_setup,
):
    client = APIClient()

    user, token, alert_groups = alert_group_internal_api_setup
    _, _, new_alert_group, _ = alert_groups

    user1 = make_user_for_organization(user.organization)
    user2 = make_user_for_organization(user.organization)

    # add paging log records
    new_alert_group.log_records.create(
        type=AlertGroupLogRecord.TYPE_DIRECT_PAGING,
        author=user,
        reason="paged user",
        step_specific_info={"user": user1.public_primary_key},
    )
    new_alert_group.log_records.create(
        type=AlertGroupLogRecord.TYPE_DIRECT_PAGING,
        author=user,
        reason="paged user",
        step_specific_info={"user": user2.public_primary_key},
    )
    new_alert_group.log_records.create(
        type=AlertGroupLogRecord.TYPE_UNPAGE_USER,
        author=user,
        reason="unpaged user",
        step_specific_info={"user": user1.public_primary_key},
    )

    url = reverse("api-internal:alertgroup-detail", kwargs={"pk": new_alert_group.public_primary_key})
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.json()["paged_users"] == [user2.short()]


@pytest.mark.django_db
def test_alert_group_resolve_resolution_note(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_alert,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(alert_receive_channel, is_default=True)
    new_alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)
    make_alert(alert_group=new_alert_group, raw_request_data=alert_raw_request_data)

    organization.is_resolution_note_required = True
    organization.save()

    client = APIClient()
    url = reverse("api-internal:alertgroup-resolve", kwargs={"pk": new_alert_group.public_primary_key})

    response = client.post(url, format="json", **make_user_auth_headers(user, token))
    # check that resolution note is required
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["code"] == AlertGroupAPIError.RESOLUTION_NOTE_REQUIRED.value

    with patch(
        "apps.alerts.tasks.send_update_resolution_note_signal.send_update_resolution_note_signal.apply_async"
    ) as mock_signal:
        url = reverse("api-internal:alertgroup-resolve", kwargs={"pk": new_alert_group.public_primary_key})
        response = client.post(
            url, format="json", data={"resolution_note": "hi"}, **make_user_auth_headers(user, token)
        )
        assert response.status_code == status.HTTP_200_OK

        assert new_alert_group.has_resolution_notes
        assert mock_signal.called
