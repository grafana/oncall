import json
from unittest.mock import call, patch

import pytest
from django.utils import timezone

from apps.alerts.models import AlertGroupLogRecord, EscalationPolicy
from apps.base.models import UserNotificationPolicyLogRecord
from apps.public_api.serializers import IncidentSerializer
from apps.webhooks.models import Webhook
from apps.webhooks.tasks import execute_webhook, send_webhook_event
from apps.webhooks.tasks.trigger_webhook import NOT_FROM_SELECTED_INTEGRATION
from settings.base import WEBHOOK_RESPONSE_LIMIT


class MockResponse:
    def __init__(self, status_code=200, content=None):
        self.status_code = status_code
        if content:
            self.content = content
        else:
            self.content = {"response": self.status_code}

    def json(self):
        return self.content


@pytest.mark.django_db
def test_send_webhook_event_filters(
    make_organization, make_team, make_alert_receive_channel, make_alert_group, make_custom_webhook
):
    organization = make_organization()
    other_organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    webhooks = {}
    for trigger_type, _ in Webhook.TRIGGER_TYPES:
        webhooks[trigger_type] = make_custom_webhook(
            organization=organization, trigger_type=trigger_type, team=make_team(organization)
        )

    for trigger_type, _ in Webhook.TRIGGER_TYPES:
        with patch("apps.webhooks.tasks.trigger_webhook.execute_webhook.apply_async") as mock_execute:
            send_webhook_event(trigger_type, alert_group.pk, organization_id=organization.pk)
        assert mock_execute.call_args == call((webhooks[trigger_type].pk, alert_group.pk, None, None))

    # other org
    other_org_webhook = make_custom_webhook(
        organization=other_organization, trigger_type=Webhook.TRIGGER_ALERT_GROUP_CREATED
    )

    alert_receive_channel = make_alert_receive_channel(other_organization)
    alert_group = make_alert_group(alert_receive_channel)
    with patch("apps.webhooks.tasks.trigger_webhook.execute_webhook.apply_async") as mock_execute:
        send_webhook_event(Webhook.TRIGGER_ALERT_GROUP_CREATED, alert_group.pk, organization_id=other_organization.pk)
    assert mock_execute.call_args == call((other_org_webhook.pk, alert_group.pk, None, None))


@pytest.mark.django_db
def test_execute_webhook_disabled(
    make_organization, make_team, make_alert_receive_channel, make_alert_group, make_custom_webhook
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_custom_webhook(organization=organization, trigger_type=Webhook.TRIGGER_ALERT_GROUP_CREATED)
    make_custom_webhook(
        organization=organization, trigger_type=Webhook.TRIGGER_ALERT_GROUP_CREATED, is_webhook_enabled=False
    )

    with patch("apps.webhooks.tasks.trigger_webhook.execute_webhook.apply_async") as mock_execute:
        send_webhook_event(Webhook.TRIGGER_ALERT_GROUP_CREATED, alert_group.pk, organization_id=organization.pk)
    mock_execute.assert_called_once()


@pytest.mark.django_db
def test_execute_webhook_integration_filter_not_matching(
    make_organization, make_team, make_alert_receive_channel, make_alert_group, make_custom_webhook
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    webhook = make_custom_webhook(
        organization=organization,
        trigger_type=Webhook.TRIGGER_ALERT_GROUP_CREATED,
        integration_filter=["does-not-match"],
    )

    with patch("apps.webhooks.models.webhook.requests") as mock_requests:
        execute_webhook(webhook.pk, alert_group.pk, None, None)

    assert not mock_requests.post.called
    # check log should exist but have no status code
    assert (
        webhook.responses.count() == 1
        and webhook.responses.first().status_code is None
        and webhook.responses.first().request_trigger == NOT_FROM_SELECTED_INTEGRATION
    )


@pytest.mark.django_db
def test_execute_webhook_integration_filter_matching(
    make_organization, make_team, make_alert_receive_channel, make_alert_group, make_custom_webhook
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization, public_primary_key="test-integration-1")
    alert_group = make_alert_group(alert_receive_channel)
    webhook = make_custom_webhook(
        organization=organization,
        trigger_type=Webhook.TRIGGER_ALERT_GROUP_CREATED,
        integration_filter=["test-integration-1"],
        # Check we get past integration filter but exit early to keep test simple
        trigger_template="False",
    )

    with patch("apps.webhooks.models.webhook.requests") as mock_requests:
        execute_webhook(webhook.pk, alert_group.pk, None, None)

    assert not mock_requests.post.called
    # check log should exist but have no status code
    assert (
        webhook.responses.count() == 1
        and webhook.responses.first().status_code is None
        # Matches evaluated trigger_template
        and webhook.responses.first().request_trigger == "False"
    )


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
            execute_webhook(webhook.pk, alert_group.pk, user.pk, None)

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
    # check log record
    log_record = alert_group.log_records.last()
    assert log_record.type == AlertGroupLogRecord.TYPE_CUSTOM_BUTTON_TRIGGERED
    expected_info = {
        "trigger": "acknowledge",
        "webhook_id": webhook.public_primary_key,
        "webhook_name": webhook.name,
    }
    assert log_record.step_specific_info == expected_info
    assert log_record.escalation_policy is None
    assert log_record.escalation_policy_step is None
    assert log_record.rendered_log_line_action() == f"outgoing webhook `{webhook.name}` triggered by acknowledge"


@pytest.mark.django_db
def test_execute_webhook_via_escalation_ok(
    make_organization,
    make_user_for_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_custom_webhook,
    make_escalation_chain,
    make_escalation_policy,
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
        trigger_type=Webhook.TRIGGER_ESCALATION_STEP,
        trigger_template="{{{{ alert_group.integration_id == '{}' }}}}".format(
            alert_receive_channel.public_primary_key
        ),
        headers='{"some-header": "{{ alert_group_id }}"}',
        data='{"value": "{{ alert_group_id }}"}',
        forward_all=False,
    )
    escalation_chain = make_escalation_chain(organization)
    escalation_policy = make_escalation_policy(
        escalation_chain=escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_TRIGGER_CUSTOM_WEBHOOK,
        custom_webhook=webhook,
    )

    mock_response = MockResponse()
    with patch("apps.webhooks.utils.socket.gethostbyname") as mock_gethostbyname:
        mock_gethostbyname.return_value = "8.8.8.8"
        with patch("apps.webhooks.models.webhook.requests") as mock_requests:
            mock_requests.post.return_value = mock_response
            execute_webhook(webhook.pk, alert_group.pk, user.pk, escalation_policy.pk)

    assert mock_requests.post.called
    # check log record
    log_record = alert_group.log_records.last()
    assert log_record.type == AlertGroupLogRecord.TYPE_CUSTOM_BUTTON_TRIGGERED
    expected_info = {
        "trigger": "escalation",
        "webhook_id": webhook.public_primary_key,
        "webhook_name": webhook.name,
    }
    assert log_record.step_specific_info == expected_info
    assert log_record.escalation_policy == escalation_policy
    assert log_record.escalation_policy_step == EscalationPolicy.STEP_TRIGGER_CUSTOM_WEBHOOK
    assert log_record.rendered_log_line_action() == f"outgoing webhook `{webhook.name}` triggered by escalation"


@pytest.mark.django_db
def test_execute_webhook_ok_forward_all(
    make_organization,
    make_user_for_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_user_notification_policy_log_record,
    make_custom_webhook,
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    notified_user = make_user_for_organization(organization)
    other_user = make_user_for_organization(organization)
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(
        alert_receive_channel, acknowledged_at=timezone.now(), acknowledged=True, acknowledged_by=user.pk
    )
    for i in range(3):
        make_user_notification_policy_log_record(
            author=notified_user,
            alert_group=alert_group,
            type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_SUCCESS,
        )
    make_user_notification_policy_log_record(
        author=other_user,
        alert_group=alert_group,
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
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
            execute_webhook(webhook.pk, alert_group.pk, user.pk, None)

    assert mock_requests.post.called
    expected_data = {
        "event": {
            "type": "acknowledge",
            "time": alert_group.acknowledged_at.isoformat(),
        },
        "user": {
            "id": user.public_primary_key,
            "username": user.username,
            "email": user.email,
        },
        "integration": {
            "id": alert_receive_channel.public_primary_key,
            "type": alert_receive_channel.integration,
            "name": alert_receive_channel.short_name,
            "team": None,
        },
        "notified_users": [
            {
                "id": notified_user.public_primary_key,
                "username": notified_user.username,
                "email": notified_user.email,
            }
        ],
        "alert_group": IncidentSerializer(alert_group).data,
        "alert_group_id": alert_group.public_primary_key,
        "alert_payload": "",
        "users_to_be_notified": [],
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
def test_execute_webhook_using_responses_data(
    make_organization,
    make_user_for_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_custom_webhook,
    make_webhook_response,
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(
        alert_receive_channel, acknowledged_at=timezone.now(), acknowledged=True, acknowledged_by=user.pk
    )
    webhook = make_custom_webhook(
        organization=organization,
        url='https://something/{{ responses["response-1"].id }}/',
        http_method="POST",
        trigger_type=Webhook.TRIGGER_RESOLVE,
        data='{"value": "{{ responses["response-2"].status }}"}',
        forward_all=False,
    )

    # add previous webhook responses for the related alert group
    make_webhook_response(
        alert_group=alert_group,
        webhook=make_custom_webhook(
            organization=organization,
            public_primary_key="response-1",
        ),
        trigger_type=Webhook.TRIGGER_ALERT_GROUP_CREATED,
        status_code=200,
        content=json.dumps({"id": "third-party-id"}),
    )
    make_webhook_response(
        alert_group=alert_group,
        webhook=make_custom_webhook(
            organization=organization,
            public_primary_key="response-2",
        ),
        trigger_type=Webhook.TRIGGER_ACKNOWLEDGE,
        status_code=200,
        content=json.dumps({"id": "third-party-id", "status": "updated"}),
    )
    # webhook wasn't executed because of some error, there is no content or status_code
    make_webhook_response(
        alert_group=alert_group,
        webhook=make_custom_webhook(
            organization=organization,
            public_primary_key="response-3",
        ),
        trigger_type=Webhook.TRIGGER_SILENCE,
        content=None,
        status_code=None,
    )

    mock_response = MockResponse()
    with patch("apps.webhooks.utils.socket.gethostbyname") as mock_gethostbyname:
        mock_gethostbyname.return_value = "8.8.8.8"
        with patch("apps.webhooks.models.webhook.requests") as mock_requests:
            mock_requests.post.return_value = mock_response
            execute_webhook(webhook.pk, alert_group.pk, user.pk, None)

    assert mock_requests.post.called
    expected_data = {"value": "updated"}
    expected_call = call(
        "https://something/third-party-id/",
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
    assert log.url == "https://something/third-party-id/"


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
        execute_webhook(webhook.pk, alert_group.pk, None, None)

    assert not mock_requests.post.called
    # check log should exist but have no status
    assert webhook.responses.count() == 1 and webhook.responses.first().status_code is None


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
            execute_webhook(webhook.pk, alert_group.pk, None, None)

    assert not mock_requests.post.called
    log = webhook.responses.all()[0]
    assert log.status_code is None
    assert log.content is None
    error = getattr(log, log_field_name)
    assert error == expected_error
    # check log record
    log_record = alert_group.log_records.last()
    assert log_record.type == AlertGroupLogRecord.ERROR_ESCALATION_TRIGGER_CUSTOM_WEBHOOK_ERROR
    expected_info = {
        "trigger": "resolve",
        "webhook_id": webhook.public_primary_key,
        "webhook_name": webhook.name,
    }
    assert log_record.step_specific_info == expected_info
    assert log_record.reason == expected_error
    assert (
        log_record.rendered_log_line_action() == f"skipped resolve outgoing webhook `{webhook.name}`: {expected_error}"
    )


@pytest.mark.django_db
def test_response_content_limit(
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
        url="https://test/",
        http_method="POST",
        trigger_type=Webhook.TRIGGER_ACKNOWLEDGE,
        forward_all=False,
    )

    content_length = 100000
    mock_response = MockResponse(content="A" * content_length)
    with patch("apps.webhooks.utils.socket.gethostbyname") as mock_gethostbyname:
        mock_gethostbyname.return_value = "8.8.8.8"
        with patch("apps.webhooks.models.webhook.requests") as mock_requests:
            mock_requests.post.return_value = mock_response
            execute_webhook(webhook.pk, alert_group.pk, user.pk, None)

    assert mock_requests.post.called
    expected_call = call(
        "https://test/",
        timeout=10,
        headers={},
    )
    assert mock_requests.post.call_args == expected_call
    # check logs
    log = webhook.responses.all()[0]
    assert log.status_code == 200
    assert log.content == f"Response content {content_length} exceeds {WEBHOOK_RESPONSE_LIMIT} character limit"
    assert log.url == "https://test/"
