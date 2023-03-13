import json
from unittest.mock import call, patch

import pytest

from apps.webhooks.models import Webhook
from apps.webhooks.tasks import execute_webhook, send_webhook_event


class MockResponse:
    def __init__(self, status_code=200):
        self.status_code = status_code

    def json(self):
        return {"response": self.status_code}


@pytest.mark.django_db
def test_send_webhook_event_filters(make_organization, make_team, make_custom_webhook):
    organization = make_organization()
    other_organization = make_organization()
    other_team = make_team(organization)

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

    sample_data = {"field": "value"}
    for trigger_type, _ in Webhook.TRIGGER_TYPES:
        with patch("apps.webhooks.tasks.trigger_webhook.execute_webhook.apply_async") as mock_execute:
            send_webhook_event(trigger_type, sample_data, organization_id=organization.pk)
        assert mock_execute.call_args == call((webhooks[trigger_type].pk, sample_data))

    # other team
    with patch("apps.webhooks.tasks.trigger_webhook.execute_webhook.apply_async") as mock_execute:
        send_webhook_event(
            Webhook.TRIGGER_ACKNOWLEDGE, sample_data, organization_id=organization.pk, team_id=other_team.pk
        )
    assert mock_execute.call_args == call((other_team_webhook.pk, sample_data))

    # other org
    with patch("apps.webhooks.tasks.trigger_webhook.execute_webhook.apply_async") as mock_execute:
        send_webhook_event(Webhook.TRIGGER_NEW, sample_data, organization_id=other_organization.pk)
    assert mock_execute.call_args == call((other_org_webhook.pk, sample_data))


@pytest.mark.django_db
def test_execute_webhook_ok(make_organization, make_custom_webhook):
    # set trigger, build_url, build_requests_args, check status/log
    organization = make_organization()
    webhook = make_custom_webhook(
        organization=organization,
        url="https://something/{{ alert_id }}/",
        http_method="POST",
        trigger_type=Webhook.TRIGGER_ACKNOWLEDGE,
        trigger_template="{{ integration_id == 'the-integration' }}",
        headers='{"some-header": "{{ alert_id }}"}',
        data='{"value": "{{ value }}"}',
        forward_all=False,
    )
    data = {
        "integration_id": "the-integration",
        "alert_id": "ID123",
        "value": "42",
    }

    mock_response = MockResponse()
    with patch("apps.webhooks.utils.socket.gethostbyname") as mock_gethostbyname:
        mock_gethostbyname.return_value = "8.8.8.8"
        with patch("apps.webhooks.models.webhook.requests") as mock_requests:
            mock_requests.post.return_value = mock_response
            execute_webhook(webhook.pk, data)

    assert mock_requests.post.called
    expected_call = call(
        "https://something/ID123/",
        timeout=10,
        headers={"some-header": "ID123"},
        json={"value": "42"},
    )
    assert mock_requests.post.call_args == expected_call
    # check logs
    log = webhook.logs.all()[0]
    assert log.response_status == "200"
    assert log.response == json.dumps(mock_response.json())
    assert log.input_data == data
    assert log.data == json.dumps({"value": "42"})
    assert log.headers == json.dumps({"some-header": "ID123"})
    assert log.url == "https://something/ID123/"


@pytest.mark.django_db
def test_execute_webhook_trigger_false(make_organization, make_custom_webhook):
    # set trigger, build_url, build_requests_args, check status/log
    organization = make_organization()
    webhook = make_custom_webhook(
        organization=organization,
        url="https://something/{{ alert_id }}/",
        http_method="POST",
        trigger_type=Webhook.TRIGGER_ACKNOWLEDGE,
        trigger_template="{{ integration_id == 'the-integration' }}",
    )
    data = {
        "integration_id": "other-integration",
        "alert_id": "ID123",
        "value": "42",
    }

    with patch("apps.webhooks.models.webhook.requests") as mock_requests:
        execute_webhook(webhook.pk, data)

    assert not mock_requests.post.called
    # check no logs
    assert webhook.logs.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field_name,value,log_field_name,expected_error",
    [
        (
            "url",
            "https://myserver/{{ alert_payload.id }}/triggered",
            "url",
            "URL - Template Warning: 'alert_payload' is undefined",
        ),
        (
            "trigger_template",
            "{{ }}",
            "trigger",
            "Trigger - Template Error: Expected an expression, got 'end of print statement'",
        ),
        ("headers", '"{{foo|invalid}}"', "headers", "Headers - Template Error: No filter named 'invalid'."),
        ("data", "{{ }}", "data", "Data - Template Error: Expected an expression, got 'end of print statement'"),
    ],
)
def test_execute_webhook_errors(
    make_organization, make_custom_webhook, field_name, value, log_field_name, expected_error
):
    organization = make_organization()
    extra_kwargs = {field_name: value}
    if "url" not in extra_kwargs:
        extra_kwargs["url"] = "https://something.cool/"
    webhook = make_custom_webhook(
        organization=organization,
        http_method="POST",
        trigger_type=Webhook.TRIGGER_ACKNOWLEDGE,
        forward_all=False,
        **extra_kwargs,
    )
    data = {
        "integration_id": "other-integration",
        "alert_id": "ID123",
        "value": "42",
    }

    with patch("apps.webhooks.utils.socket.gethostbyname") as mock_gethostbyname:
        # make it a valid URL when resolving name
        mock_gethostbyname.return_value = "8.8.8.8"
        with patch("apps.webhooks.models.webhook.requests") as mock_requests:
            execute_webhook(webhook.pk, data)

    assert not mock_requests.post.called
    log = webhook.logs.all()[0]
    assert log.response_status is None
    assert log.response is None
    assert log.input_data == data
    error = getattr(log, log_field_name)
    assert error == expected_error
