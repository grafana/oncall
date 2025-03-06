from unittest.mock import patch

import httpretty
import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.alerts.constants import ActionSource
from apps.alerts.models import AlertGroup, AlertReceiveChannel
from apps.alerts.tasks import delete_alert_group, wipe
from apps.api import permissions
from apps.auth_token.tests.helpers import setup_service_account_api_mocks


def construct_expected_response_from_alert_groups(alert_groups):
    results = []
    for alert_group in alert_groups:
        # convert datetimes to serializers.DateTimeField
        created_at = None
        if alert_group.started_at:
            created_at = alert_group.started_at.isoformat()
            created_at = created_at[:-6] + "Z"

        resolved_at = None
        if alert_group.resolved_at:
            resolved_at = alert_group.resolved_at.isoformat()
            resolved_at = resolved_at[:-6] + "Z"

        acknowledged_at = None
        if alert_group.acknowledged_at:
            acknowledged_at = alert_group.acknowledged_at.isoformat()
            acknowledged_at = acknowledged_at[:-6] + "Z"

        silenced_at = None
        if alert_group.silenced_at:
            silenced_at = alert_group.silenced_at.isoformat()
            silenced_at = silenced_at[:-6] + "Z"

        def user_pk_or_none(alert_group, user_field):
            u = getattr(alert_group, user_field)
            if u is not None:
                return u.public_primary_key

        labels = []
        for label in alert_group.labels.all():
            labels.append(
                {
                    "key": {"id": label.key_name, "name": label.key_name},
                    "value": {"id": label.value_name, "name": label.value_name},
                }
            )

        results.append(
            {
                "id": alert_group.public_primary_key,
                "integration_id": alert_group.channel.public_primary_key,
                "team_id": alert_group.channel.team.public_primary_key if alert_group.channel.team else None,
                "route_id": alert_group.channel_filter.public_primary_key,
                "alerts_count": alert_group.alerts.count(),
                "state": alert_group.state,
                "created_at": created_at,
                "resolved_at": resolved_at,
                "acknowledged_at": acknowledged_at,
                "acknowledged_by": user_pk_or_none(alert_group, "acknowledged_by_user"),
                "resolved_by": user_pk_or_none(alert_group, "resolved_by_user"),
                "title": None,
                "labels": labels,
                "permalinks": {
                    "slack": None,
                    "slack_app": None,
                    "telegram": None,
                    "web": alert_group.web_link,
                },
                "silenced_at": silenced_at,
                "last_alert": {
                    "id": alert_group.alerts.last().public_primary_key,
                    "alert_group_id": alert_group.public_primary_key,
                    "created_at": alert_group.alerts.last().created_at.isoformat().replace("+00:00", "Z"),
                    "payload": alert_group.channel.config.example_payload,
                },
            }
        )
    return {
        "count": len(alert_groups),
        "next": None,
        "previous": None,
        "results": results,
        "current_page_number": 1,
        "page_size": 50,
        "total_pages": 1,
    }


@pytest.fixture()
def alert_group_public_api_setup(
    make_organization_and_user_with_token,
    make_team,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_alert,
):
    organization, user, token = make_organization_and_user_with_token()
    team = make_team(organization)
    grafana = make_alert_receive_channel(organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA)
    formatted_webhook = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_FORMATTED_WEBHOOK, team=team
    )

    grafana_default_route = make_channel_filter(grafana, is_default=True)
    grafana_non_default_route = make_channel_filter(grafana, filtering_term="us-east")
    formatted_webhook_default_route = make_channel_filter(formatted_webhook, is_default=True)

    grafana_alert_group_default_route = make_alert_group(grafana, channel_filter=grafana_default_route)
    grafana_alert_group_non_default_route = make_alert_group(grafana, channel_filter=grafana_non_default_route)
    formatted_webhook_alert_group = make_alert_group(formatted_webhook, channel_filter=formatted_webhook_default_route)

    make_alert(alert_group=grafana_alert_group_default_route, raw_request_data=grafana.config.example_payload)
    make_alert(alert_group=grafana_alert_group_non_default_route, raw_request_data=grafana.config.example_payload)
    make_alert(alert_group=formatted_webhook_alert_group, raw_request_data=formatted_webhook.config.example_payload)

    integrations = grafana, formatted_webhook
    alert_groups = (
        grafana_alert_group_default_route,
        grafana_alert_group_non_default_route,
        formatted_webhook_alert_group,
    )
    routes = grafana_default_route, grafana_non_default_route, formatted_webhook_default_route

    return token, alert_groups, integrations, routes


@pytest.mark.django_db
def test_get_alert_group(alert_group_public_api_setup):
    token, _, _, _ = alert_group_public_api_setup
    alert_groups = AlertGroup.objects.all().order_by("-started_at")
    client = APIClient()
    list_response = construct_expected_response_from_alert_groups(alert_groups)
    expected_response = list_response["results"][0]

    url = reverse("api-public:alert_groups-detail", kwargs={"pk": expected_response["id"]})
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_alert_group_slack_links(
    alert_group_public_api_setup, make_slack_team_identity, make_slack_channel, make_slack_message
):
    token, _, _, _ = alert_group_public_api_setup
    alert_group = AlertGroup.objects.all().order_by("-started_at").first()
    organization = alert_group.channel.organization
    client = APIClient()
    list_response = construct_expected_response_from_alert_groups(AlertGroup.objects.filter(pk=alert_group.pk))
    expected_response = list_response["results"][0]

    slack_team_identity = make_slack_team_identity()
    organization.slack_team_identity = slack_team_identity
    organization.save()
    slack_channel = make_slack_channel(slack_team_identity)
    slack_message = make_slack_message(slack_channel, alert_group=alert_group, cached_permalink="the-link")

    url = reverse("api-public:alert_groups-detail", kwargs={"pk": expected_response["id"]})
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    expected_response["permalinks"]["slack"] = slack_message.permalink
    expected_response["permalinks"]["slack_app"] = slack_message.deep_link
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_alert_groups(alert_group_public_api_setup):
    token, _, _, _ = alert_group_public_api_setup
    alert_groups = AlertGroup.objects.all().order_by("-started_at")
    client = APIClient()
    expected_response = construct_expected_response_from_alert_groups(alert_groups)

    url = reverse("api-public:alert_groups-list")
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_alert_groups_inactive_user(make_organization_and_user_with_token):
    _, user, token = make_organization_and_user_with_token()
    # user is set to inactive if deleted via queryset (ie. during sync)
    user.is_active = False
    user.save()

    client = APIClient()
    url = reverse("api-public:alert_groups-list")
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_get_alert_groups_include_labels(alert_group_public_api_setup, make_alert_group_label_association):
    token, _, _, _ = alert_group_public_api_setup
    alert_groups = AlertGroup.objects.all().order_by("-started_at")
    alert_group_0 = alert_groups[0]
    organization = alert_group_0.channel.organization
    # set labels for the first alert group
    make_alert_group_label_association(organization, alert_group_0, key_name="a", value_name="b")

    client = APIClient()
    expected_response = construct_expected_response_from_alert_groups(alert_groups)

    url = reverse("api-public:alert_groups-list")
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_alert_groups_filter_by_integration(
    alert_group_public_api_setup,
):
    token, alert_groups, integrations, _ = alert_group_public_api_setup
    formatted_webhook = integrations[1]
    alert_groups = AlertGroup.objects.filter(channel=formatted_webhook).order_by("-started_at")
    expected_response = construct_expected_response_from_alert_groups(alert_groups)
    client = APIClient()

    url = reverse("api-public:alert_groups-list")
    response = client.get(
        url + f"?integration_id={formatted_webhook.public_primary_key}", format="json", HTTP_AUTHORIZATION=token
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_alert_groups_filter_by_team(alert_group_public_api_setup):
    token, alert_groups, integrations, _ = alert_group_public_api_setup

    for integration in integrations:
        team_id = integration.team.public_primary_key if integration.team else "null"
        alert_groups = AlertGroup.objects.filter(channel=integration).order_by("-started_at")
        expected_response = construct_expected_response_from_alert_groups(alert_groups)

        client = APIClient()
        url = reverse("api-public:alert_groups-list")
        response = client.get(url + f"?team_id={team_id}", format="json", HTTP_AUTHORIZATION=token)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == expected_response


@pytest.mark.django_db
def test_get_alert_groups_filter_by_started_at(alert_group_public_api_setup):
    token, alert_groups, _, _ = alert_group_public_api_setup
    now = timezone.now()
    # set custom started_at dates
    for i, alert_group in enumerate(alert_groups):
        # alert groups starting every 10 days going back
        alert_group.started_at = now - timezone.timedelta(days=10 * i + 1)
        alert_group.save(update_fields=["started_at"])

    client = APIClient()
    url = reverse("api-public:alert_groups-list")
    ranges = (
        # start, end, expected
        (now - timezone.timedelta(days=1), now, [alert_groups[0]]),
        (now - timezone.timedelta(days=12), now, [alert_groups[0], alert_groups[1]]),
        (now - timezone.timedelta(days=12), now - timezone.timedelta(days=5), [alert_groups[1]]),
        (now - timezone.timedelta(days=32), now, alert_groups),
    )

    for range_start, range_end, expected_alert_groups in ranges:
        started_at_q = "?started_at={}_{}".format(
            range_start.strftime("%Y-%m-%dT%H:%M:%S"), range_end.strftime("%Y-%m-%dT%H:%M:%S")
        )
        response = client.get(url + started_at_q, format="json", HTTP_AUTHORIZATION=token)

        expected_response = construct_expected_response_from_alert_groups(expected_alert_groups)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == expected_response


@pytest.mark.django_db
def test_get_alert_groups_filter_by_state_new(
    alert_group_public_api_setup,
):
    token, _, _, _ = alert_group_public_api_setup
    alert_groups = AlertGroup.objects.filter(AlertGroup.get_new_state_filter()).order_by("-started_at")
    expected_response = construct_expected_response_from_alert_groups(alert_groups)
    client = APIClient()

    url = reverse("api-public:alert_groups-list")
    response = client.get(url + "?state=new", format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_alert_groups_filter_by_state_acknowledged(
    alert_group_public_api_setup,
):
    token, _, _, _ = alert_group_public_api_setup
    alert_groups = AlertGroup.objects.filter(AlertGroup.get_acknowledged_state_filter()).order_by("-started_at")
    expected_response = construct_expected_response_from_alert_groups(alert_groups)
    client = APIClient()

    url = reverse("api-public:alert_groups-list")
    response = client.get(url + "?state=acknowledged", format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_alert_groups_filter_by_state_silenced(
    alert_group_public_api_setup,
):
    token, _, _, _ = alert_group_public_api_setup
    alert_groups = AlertGroup.objects.filter(AlertGroup.get_silenced_state_filter()).order_by("-started_at")
    expected_response = construct_expected_response_from_alert_groups(alert_groups)
    client = APIClient()

    url = reverse("api-public:alert_groups-list")
    response = client.get(url + "?state=silenced", format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_alert_groups_filter_by_state_resolved(
    alert_group_public_api_setup,
):
    token, _, _, _ = alert_group_public_api_setup
    alert_groups = AlertGroup.objects.filter(AlertGroup.get_resolved_state_filter()).order_by("-started_at")
    expected_response = construct_expected_response_from_alert_groups(alert_groups)
    client = APIClient()

    url = reverse("api-public:alert_groups-list")
    response = client.get(url + "?state=resolved", format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_alert_groups_filter_by_state_unknown(
    alert_group_public_api_setup,
):
    token, _, _, _ = alert_group_public_api_setup
    client = APIClient()

    url = reverse("api-public:alert_groups-list")
    response = client.get(url + "?state=unknown", format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_get_alert_groups_filter_by_integration_no_result(
    alert_group_public_api_setup,
):
    token, _, _, _ = alert_group_public_api_setup
    client = APIClient()

    url = reverse("api-public:alert_groups-list")
    response = client.get(url + "?integration_id=impossible_integration", format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"] == []


@pytest.mark.django_db
def test_get_alert_groups_filter_by_route(
    alert_group_public_api_setup,
):
    token, alert_groups, integrations, routes = alert_group_public_api_setup
    grafana_non_default_route = routes[1]
    alert_groups = AlertGroup.objects.filter(channel_filter=grafana_non_default_route).order_by("-started_at")
    expected_response = construct_expected_response_from_alert_groups(alert_groups)
    client = APIClient()

    url = reverse("api-public:alert_groups-list")
    response = client.get(
        url + f"?route_id={grafana_non_default_route.public_primary_key}", format="json", HTTP_AUTHORIZATION=token
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_alert_groups_filter_by_route_no_result(
    alert_group_public_api_setup,
):
    token, _, _, _ = alert_group_public_api_setup
    client = APIClient()

    url = reverse("api-public:alert_groups-list")
    response = client.get(url + "?route_id=impossible_route_ir", format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"] == []


@pytest.mark.django_db
def test_get_alert_groups_filter_by_labels(
    alert_group_public_api_setup,
    make_alert_group_label_association,
):
    token, alert_groups, _, _ = alert_group_public_api_setup

    organization = alert_groups[0].channel.organization
    make_alert_group_label_association(organization, alert_groups[0], key_name="a", value_name="b")
    make_alert_group_label_association(organization, alert_groups[0], key_name="c", value_name="d")
    make_alert_group_label_association(organization, alert_groups[1], key_name="a", value_name="b")
    make_alert_group_label_association(organization, alert_groups[2], key_name="c", value_name="d")
    expected_response = construct_expected_response_from_alert_groups([alert_groups[0]])

    client = APIClient()
    url = reverse("api-public:alert_groups-list")
    response = client.get(url + "?label=a:b&label=c:d", format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.parametrize(
    "data,task,status_code",
    [
        (None, wipe, status.HTTP_204_NO_CONTENT),
        ({"mode": "wipe"}, wipe, status.HTTP_204_NO_CONTENT),
        ({"mode": "delete"}, delete_alert_group, status.HTTP_204_NO_CONTENT),
        ({"mode": "random"}, None, status.HTTP_400_BAD_REQUEST),
        ("delete", None, status.HTTP_400_BAD_REQUEST),
    ],
)
@pytest.mark.django_db
def test_delete_alert_group(alert_group_public_api_setup, data, task, status_code):
    token, alert_groups, _, _ = alert_group_public_api_setup
    alert_group = alert_groups[0]

    client = APIClient()
    url = reverse("api-public:alert_groups-detail", kwargs={"pk": alert_group.public_primary_key})

    if task:
        with patch.object(task, "apply_async") as mock_task:
            response = client.delete(url, data=data, format="json", HTTP_AUTHORIZATION=token)
            mock_task.assert_called_once()
    else:
        response = client.delete(url, data=data, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status_code


@pytest.mark.django_db
def test_pagination(settings, alert_group_public_api_setup):
    settings.BASE_URL = "https://test.com/test/prefixed/urls"

    token, alert_groups, _, _ = alert_group_public_api_setup
    client = APIClient()

    url = "{}?perpage=1".format(reverse("api-public:alert_groups-list"))

    response = client.get(url, HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    result = response.json()

    assert result["next"].startswith("https://test.com/test/prefixed/urls")


@pytest.mark.parametrize(
    "acknowledged,resolved,attached,maintenance,status_code",
    [
        (False, False, False, False, status.HTTP_200_OK),
        (True, False, False, False, status.HTTP_400_BAD_REQUEST),
        (False, True, False, False, status.HTTP_400_BAD_REQUEST),
        (False, False, True, False, status.HTTP_400_BAD_REQUEST),
        (False, False, False, True, status.HTTP_400_BAD_REQUEST),
    ],
)
@pytest.mark.django_db
def test_alert_group_acknowledge(
    make_organization_and_user_with_token,
    make_alert_receive_channel,
    make_alert_group,
    acknowledged,
    resolved,
    attached,
    maintenance,
    status_code,
):
    organization, _, token = make_organization_and_user_with_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    root_alert_group = make_alert_group(alert_receive_channel)
    alert_group = make_alert_group(
        alert_receive_channel,
        acknowledged=acknowledged,
        resolved=resolved,
        root_alert_group=root_alert_group if attached else None,
        maintenance_uuid="test_maintenance_uuid" if maintenance else None,
    )

    client = APIClient()
    url = reverse("api-public:alert_groups-acknowledge", kwargs={"pk": alert_group.public_primary_key})
    response = client.post(url, HTTP_AUTHORIZATION=token)
    assert response.status_code == status_code

    if status_code == status.HTTP_200_OK:
        alert_group.refresh_from_db()
        assert alert_group.acknowledged is True
        assert alert_group.log_records.last().action_source == ActionSource.API


@pytest.mark.parametrize(
    "acknowledged,resolved,attached,maintenance,status_code",
    [
        (True, False, False, False, status.HTTP_200_OK),
        (True, True, False, False, status.HTTP_400_BAD_REQUEST),
        (True, False, True, False, status.HTTP_400_BAD_REQUEST),
        (True, False, False, True, status.HTTP_400_BAD_REQUEST),
        (False, False, False, False, status.HTTP_400_BAD_REQUEST),
    ],
)
@pytest.mark.django_db
def test_alert_group_unacknowledge(
    make_organization_and_user_with_token,
    make_alert_receive_channel,
    make_alert_group,
    acknowledged,
    resolved,
    attached,
    maintenance,
    status_code,
):
    organization, _, token = make_organization_and_user_with_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    root_alert_group = make_alert_group(alert_receive_channel)
    alert_group = make_alert_group(
        alert_receive_channel,
        acknowledged=acknowledged,
        resolved=resolved,
        root_alert_group=root_alert_group if attached else None,
        maintenance_uuid="test_maintenance_uuid" if maintenance else None,
    )

    client = APIClient()
    url = reverse("api-public:alert_groups-unacknowledge", kwargs={"pk": alert_group.public_primary_key})
    response = client.post(url, HTTP_AUTHORIZATION=token)
    assert response.status_code == status_code

    if status_code == status.HTTP_200_OK:
        alert_group.refresh_from_db()
        assert alert_group.acknowledged is False
        assert alert_group.log_records.last().action_source == ActionSource.API


@pytest.mark.parametrize(
    "resolved,attached,maintenance,status_code",
    [
        (False, False, False, status.HTTP_200_OK),
        (False, False, True, status.HTTP_200_OK),
        (True, False, False, status.HTTP_400_BAD_REQUEST),
        (False, True, False, status.HTTP_400_BAD_REQUEST),
    ],
)
@pytest.mark.django_db
def test_alert_group_resolve(
    make_organization_and_user_with_token,
    make_alert_receive_channel,
    make_alert_group,
    resolved,
    attached,
    maintenance,
    status_code,
):
    organization, _, token = make_organization_and_user_with_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    root_alert_group = make_alert_group(alert_receive_channel)
    alert_group = make_alert_group(
        alert_receive_channel,
        resolved=resolved,
        root_alert_group=root_alert_group if attached else None,
        maintenance_uuid="test_maintenance_uuid" if maintenance else None,
    )

    client = APIClient()
    url = reverse("api-public:alert_groups-resolve", kwargs={"pk": alert_group.public_primary_key})
    response = client.post(url, HTTP_AUTHORIZATION=token)
    assert response.status_code == status_code

    if status_code == status.HTTP_200_OK and not maintenance:
        alert_group.refresh_from_db()
        assert alert_group.resolved is True
        assert alert_group.log_records.last().action_source == ActionSource.API


@pytest.mark.parametrize(
    "resolved,attached,maintenance,status_code",
    [
        (True, False, False, status.HTTP_200_OK),
        (True, True, False, status.HTTP_400_BAD_REQUEST),
        (True, False, True, status.HTTP_400_BAD_REQUEST),
        (False, False, False, status.HTTP_400_BAD_REQUEST),
    ],
)
@pytest.mark.django_db
def test_alert_group_unresolve(
    make_organization_and_user_with_token,
    make_alert_receive_channel,
    make_alert_group,
    resolved,
    attached,
    maintenance,
    status_code,
):
    organization, _, token = make_organization_and_user_with_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    root_alert_group = make_alert_group(alert_receive_channel)
    alert_group = make_alert_group(
        alert_receive_channel,
        resolved=resolved,
        root_alert_group=root_alert_group if attached else None,
        maintenance_uuid="test_maintenance_uuid" if maintenance else None,
    )

    client = APIClient()
    url = reverse("api-public:alert_groups-unresolve", kwargs={"pk": alert_group.public_primary_key})
    response = client.post(url, HTTP_AUTHORIZATION=token)
    assert response.status_code == status_code

    if status_code == status.HTTP_200_OK:
        alert_group.refresh_from_db()
        assert alert_group.resolved is False
        assert alert_group.log_records.last().action_source == ActionSource.API


@pytest.mark.parametrize(
    "acknowledged,resolved,attached,status_code,data,response_msg",
    [
        (False, False, False, status.HTTP_200_OK, {"delay": 60}, None),
        (False, False, False, status.HTTP_400_BAD_REQUEST, {"delay": -2}, "invalid delay value"),
        (False, False, False, status.HTTP_400_BAD_REQUEST, {"delay": "fuzz"}, "invalid delay value"),
        (False, False, False, status.HTTP_400_BAD_REQUEST, {}, "delay is required"),
        (True, False, False, status.HTTP_400_BAD_REQUEST, {"delay": 60}, "Can't silence an acknowledged alert group"),
        (False, True, False, status.HTTP_400_BAD_REQUEST, {"delay": 60}, "Can't silence a resolved alert group"),
        (False, False, True, status.HTTP_400_BAD_REQUEST, {"delay": 60}, "Can't silence an attached alert group"),
    ],
)
@pytest.mark.django_db
def test_alert_group_silence(
    make_organization_and_user_with_token,
    make_alert_receive_channel,
    make_alert_group,
    acknowledged,
    resolved,
    attached,
    status_code,
    data,
    response_msg,
):
    organization, _, token = make_organization_and_user_with_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    root_alert_group = make_alert_group(alert_receive_channel)
    alert_group = make_alert_group(
        alert_receive_channel,
        acknowledged=acknowledged,
        resolved=resolved,
        root_alert_group=root_alert_group if attached else None,
    )

    client = APIClient()
    url = reverse("api-public:alert_groups-silence", kwargs={"pk": alert_group.public_primary_key})
    response = client.post(url, data=data, HTTP_AUTHORIZATION=token)

    if status_code == status.HTTP_200_OK:
        alert_group.refresh_from_db()
        assert alert_group.silenced is True
        assert alert_group.log_records.last().action_source == ActionSource.API
    else:
        assert alert_group.silenced is False
        assert response.status_code == status_code
        assert response_msg == response.json()["detail"]


@pytest.mark.parametrize(
    "silenced,resolved,acknowledged,attached,status_code,response_msg",
    [
        (True, False, False, False, status.HTTP_200_OK, None),
        (False, False, False, False, status.HTTP_400_BAD_REQUEST, "Can't unsilence an unsilenced alert group"),
        (True, True, False, False, status.HTTP_400_BAD_REQUEST, "Can't unsilence a resolved alert group"),
        (True, False, True, False, status.HTTP_400_BAD_REQUEST, "Can't unsilence an acknowledged alert group"),
        (True, False, False, True, status.HTTP_400_BAD_REQUEST, "Can't unsilence an attached alert group"),
    ],
)
@pytest.mark.django_db
def test_alert_group_unsilence(
    make_organization_and_user_with_token,
    make_alert_receive_channel,
    make_alert_group,
    silenced,
    resolved,
    acknowledged,
    attached,
    status_code,
    response_msg,
):
    organization, _, token = make_organization_and_user_with_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    root_alert_group = make_alert_group(alert_receive_channel)
    alert_group = make_alert_group(
        alert_receive_channel,
        acknowledged=acknowledged,
        resolved=resolved,
        silenced=silenced,
        root_alert_group=root_alert_group if attached else None,
    )

    client = APIClient()
    url = reverse("api-public:alert_groups-unsilence", kwargs={"pk": alert_group.public_primary_key})
    response = client.post(url, HTTP_AUTHORIZATION=token)

    if status_code == status.HTTP_200_OK:
        alert_group.refresh_from_db()
        assert alert_group.silenced is False
        assert alert_group.log_records.last().action_source == ActionSource.API
    else:
        assert alert_group.silenced == silenced
        assert response.status_code == status_code
        assert response_msg == response.json()["detail"]


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_actions_disabled_for_service_accounts(
    make_organization,
    make_service_account_for_organization,
    make_token_for_service_account,
    make_escalation_chain,
):
    organization = make_organization(grafana_url="http://grafana.test")
    service_account = make_service_account_for_organization(organization)
    token_string = "glsa_token"
    make_token_for_service_account(service_account, token_string)
    make_escalation_chain(organization)

    perms = {
        permissions.RBACPermission.Permissions.ALERT_GROUPS_WRITE.value: ["*"],
    }
    setup_service_account_api_mocks(organization.grafana_url, perms=perms)

    client = APIClient()
    disabled_actions = ["acknowledge", "unacknowledge", "resolve", "unresolve", "silence", "unsilence"]
    for action in disabled_actions:
        url = reverse(f"api-public:alert_groups-{action}", kwargs={"pk": "ABCDEFG"})
        response = client.post(
            url,
            HTTP_AUTHORIZATION=f"{token_string}",
            HTTP_X_GRAFANA_URL=organization.grafana_url,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
