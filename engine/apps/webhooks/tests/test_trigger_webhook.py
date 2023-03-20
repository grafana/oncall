import json
from unittest.mock import call, patch

import pytest
from django.utils import timezone

from apps.public_api.serializers import IncidentSerializer
from apps.webhooks.models import Webhook
from apps.webhooks.tasks import execute_webhook, send_webhook_event


class MockResponse:
    def __init__(self, status_code=200):
        self.status_code = status_code

    def json(self):
        return {"response": self.status_code}


@pytest.mark.django_db
def test_send_webhook_event_filters(
    make_organization, make_team, make_alert_receive_channel, make_alert_group, make_custom_webhook
):
    organization = make_organization()
    other_organization = make_organization()
    other_team = make_team(organization)
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    webhooks = {}
    for trigger_type, _ in Webhook.TRIGGER_TYPES:
        webhooks[trigger_type] = make_custom_webhook(
            organization=organization,
            trigger_type=trigger_type,
        )

    other_team_webhook = make_custom_webhook(
        organization=organization, team=other_team, trigger_type=Webhook.TRIGGER_ACKNOWLEDGE
    )
    other_org_webhook = make_custom_webhook(organization=other_organization, trigger_type=Webhook.TRIGGER_NEW)

    for trigger_type, _ in Webhook.TRIGGER_TYPES:
        with patch("apps.webhooks.tasks.trigger_webhook.execute_webhook.apply_async") as mock_execute:
            send_webhook_event(trigger_type, alert_group.pk, organization_id=organization.pk)
        assert mock_execute.call_args == call((webhooks[trigger_type].pk, alert_group.pk, None))

    # other team
    alert_receive_channel = make_alert_receive_channel(organization, team=other_team)
    alert_group = make_alert_group(alert_receive_channel)
    with patch("apps.webhooks.tasks.trigger_webhook.execute_webhook.apply_async") as mock_execute:
        send_webhook_event(
            Webhook.TRIGGER_ACKNOWLEDGE, alert_group.pk, organization_id=organization.pk, team_id=other_team.pk
        )
    assert mock_execute.call_args == call((other_team_webhook.pk, alert_group.pk, None))

    # other org
    alert_receive_channel = make_alert_receive_channel(other_organization)
    alert_group = make_alert_group(alert_receive_channel)
    with patch("apps.webhooks.tasks.trigger_webhook.execute_webhook.apply_async") as mock_execute:
        send_webhook_event(Webhook.TRIGGER_NEW, alert_group.pk, organization_id=other_organization.pk)
    assert mock_execute.call_args == call((other_org_webhook.pk, alert_group.pk, None))


@pytest.mark.django_db
def test_execute_webhook_ok(
    make_organization, make_user_for_organization, make_alert_receive_channel, make_alert_group, make_custom_webhook
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(
        alert_receive_channel, acknowledged_at=timezone.now(), acknowledged=True, acknowledged_by=user.pk
    )
    webhook = make_custom_webhook(
        organization=organization,
        url="https://something/{{ alert_group_id }}/",
        http_method="POST",
        trigger_type=Webhook.TRIGGER_ACKNOWLEDGE,
        trigger_template="{{{{ alert_group.integration_id == '{}' }}}}".format(
            alert_receive_channel.public_primary_key
        ),
        headers='{"some-header": "{{ alert_group_id }}"}',
        data='{"value": "{{ alert_group_id }}"}',
        forward_all=False,
    )

    mock_response = MockResponse()
    with patch("apps.webhooks.utils.socket.gethostbyname") as mock_gethostbyname:
        mock_gethostbyname.return_value = "8.8.8.8"
        with patch("apps.webhooks.models.webhook.requests") as mock_requests:
            mock_requests.post.return_value = mock_response
            execute_webhook(webhook.pk, alert_group.pk, user.pk)

    assert mock_requests.post.called
    expected_call = call(
        "https://something/{}/".format(alert_group.public_primary_key),
        timeout=10,
        headers={"some-header": alert_group.public_primary_key},
        json={"value": alert_group.public_primary_key},
    )
    assert mock_requests.post.call_args == expected_call
    # check logs
    log = webhook.responses.all()[0]
    assert log.status_code == 200
    assert log.content == json.dumps(mock_response.json())
    assert log.request_data == json.dumps({"value": alert_group.public_primary_key})
    assert log.request_headers == json.dumps({"some-header": alert_group.public_primary_key})
    assert log.url == "https://something/{}/".format(alert_group.public_primary_key)


@pytest.mark.django_db
def test_execute_webhook_ok_forward_all(
    make_organization, make_user_for_organization, make_alert_receive_channel, make_alert_group, make_custom_webhook
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(
        alert_receive_channel, acknowledged_at=timezone.now(), acknowledged=True, acknowledged_by=user.pk
    )
    webhook = make_custom_webhook(
        organization=organization,
        url="https://something/{{ alert_group_id }}/",
        http_method="POST",
        trigger_type=Webhook.TRIGGER_ACKNOWLEDGE,
        forward_all=True,
    )

    mock_response = MockResponse()
    with patch("apps.webhooks.utils.socket.gethostbyname") as mock_gethostbyname:
        mock_gethostbyname.return_value = "8.8.8.8"
        with patch("apps.webhooks.models.webhook.requests") as mock_requests:
            mock_requests.post.return_value = mock_response
            execute_webhook(webhook.pk, alert_group.pk, user.pk)

    assert mock_requests.post.called
    expected_data = {
        "event": {
            "type": "Acknowledge",
            "time": alert_group.acknowledged_at.isoformat(),
        },
        "user": user.username,
        "alert_group": IncidentSerializer(alert_group).data,
        "alert_group_id": alert_group.public_primary_key,
        "alert_payload": "",
    }
    expected_call = call(
        "https://something/{}/".format(alert_group.public_primary_key),
        timeout=10,
        headers={},
        json=expected_data,
    )
    assert mock_requests.post.call_args == expected_call
    # check logs
    log = webhook.responses.all()[0]
    assert log.status_code == 200
    assert log.content == json.dumps(mock_response.json())
    assert json.loads(log.request_data) == expected_data
    assert log.url == "https://something/{}/".format(alert_group.public_primary_key)


@pytest.mark.django_db
def test_execute_webhook_trigger_false(
    make_organization, make_alert_receive_channel, make_alert_group, make_custom_webhook
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel, acknowledged_at=timezone.now(), acknowledged=True)
    webhook = make_custom_webhook(
        organization=organization,
        url="https://something/{{ alert_id }}/",
        http_method="POST",
        trigger_type=Webhook.TRIGGER_ACKNOWLEDGE,
        trigger_template="{{ integration_id == 'the-integration' }}",
    )

    with patch("apps.webhooks.models.webhook.requests") as mock_requests:
        execute_webhook(webhook.pk, alert_group.pk, None)

    assert not mock_requests.post.called
    # check no logs
    assert webhook.responses.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field_name,value,log_field_name,expected_error",
    [
        (
            "url",
            "https://myserver/{{ }}/triggered",
            "url",
            "URL - Template Error: Expected an expression, got 'end of print statement'",
        ),
        (
            "trigger_template",
            "{{ }}",
            "request_trigger",
            "Trigger - Template Error: Expected an expression, got 'end of print statement'",
        ),
        ("headers", '"{{foo|invalid}}"', "request_headers", "Headers - Template Error: No filter named 'invalid'."),
        (
            "data",
            "{{ }}",
            "request_data",
            "Data - Template Error: Expected an expression, got 'end of print statement'",
        ),
    ],
)
def test_execute_webhook_errors(
    make_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_custom_webhook,
    field_name,
    value,
    log_field_name,
    expected_error,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel, resolved_at=timezone.now(), resolved=True)

    extra_kwargs = {field_name: value}
    if "url" not in extra_kwargs:
        extra_kwargs["url"] = "https://something.cool/"
    webhook = make_custom_webhook(
        organization=organization,
        http_method="POST",
        trigger_type=Webhook.TRIGGER_RESOLVE,
        forward_all=False,
        **extra_kwargs,
    )

    with patch("apps.webhooks.utils.socket.gethostbyname") as mock_gethostbyname:
        # make it a valid URL when resolving name
        mock_gethostbyname.return_value = "8.8.8.8"
        with patch("apps.webhooks.models.webhook.requests") as mock_requests:
            execute_webhook(webhook.pk, alert_group.pk, None)

    assert not mock_requests.post.called
    log = webhook.responses.all()[0]
    assert log.status_code is None
    assert log.content is None
    error = getattr(log, log_field_name)
    assert error == expected_error
