import json
from datetime import timedelta
from unittest.mock import call, patch

import httpretty
import pytest
import requests
from django.utils import timezone

from apps.alerts.models import AlertGroupExternalID, AlertGroupLogRecord, EscalationPolicy
from apps.base.models import UserNotificationPolicyLogRecord
from apps.public_api.serializers import IncidentSerializer
from apps.webhooks.models import Webhook
from apps.webhooks.models.webhook import WebhookSession
from apps.webhooks.tasks import execute_webhook, send_webhook_event
from apps.webhooks.tasks.trigger_webhook import NOT_FROM_SELECTED_INTEGRATION
from settings.base import WEBHOOK_RESPONSE_LIMIT

TIMEOUT = 4


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
    trigger_types = [t for t, _ in Webhook.TRIGGER_TYPES if t != Webhook.TRIGGER_STATUS_CHANGE]

    webhooks = {}
    for trigger_type in trigger_types:
        webhooks[trigger_type] = make_custom_webhook(
            organization=organization,
            trigger_type=trigger_type,
            team=make_team(organization),
            is_from_connected_integration=(trigger_type != Webhook.TRIGGER_ACKNOWLEDGE),
        )

    for trigger_type in trigger_types:
        with patch("apps.webhooks.tasks.trigger_webhook.execute_webhook.apply_async") as mock_execute:
            send_webhook_event(trigger_type, alert_group.pk, organization_id=organization.pk)
        assert mock_execute.call_args == call(
            (webhooks[trigger_type].pk, alert_group.pk, None, None), kwargs={"trigger_type": trigger_type}
        )

    # backsync event exclude connected integration webhooks
    for trigger_type in trigger_types:
        with patch("apps.webhooks.tasks.trigger_webhook.execute_webhook.apply_async") as mock_execute:
            send_webhook_event(trigger_type, alert_group.pk, organization_id=organization.pk, is_backsync=True)
            if trigger_type == Webhook.TRIGGER_ACKNOWLEDGE:
                assert mock_execute.call_args == call(
                    (webhooks[trigger_type].pk, alert_group.pk, None, None), kwargs={"trigger_type": trigger_type}
                )
            else:
                # except for the acknowledge webhook (not connected integration set), the webhook is not triggered
                mock_execute.assert_not_called()

    # other org
    other_org_webhook = make_custom_webhook(
        organization=other_organization, trigger_type=Webhook.TRIGGER_ALERT_GROUP_CREATED
    )

    alert_receive_channel = make_alert_receive_channel(other_organization)
    alert_group = make_alert_group(alert_receive_channel)
    with patch("apps.webhooks.tasks.trigger_webhook.execute_webhook.apply_async") as mock_execute:
        send_webhook_event(Webhook.TRIGGER_ALERT_GROUP_CREATED, alert_group.pk, organization_id=other_organization.pk)
    assert mock_execute.call_args == call(
        (other_org_webhook.pk, alert_group.pk, None, None), kwargs={"trigger_type": Webhook.TRIGGER_ALERT_GROUP_CREATED}
    )


@pytest.mark.django_db
def test_send_webhook_event_status_change(
    make_organization, make_team, make_alert_receive_channel, make_alert_group, make_custom_webhook
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    webhooks = {}
    for trigger_type, _ in Webhook.TRIGGER_TYPES:
        webhooks[trigger_type] = make_custom_webhook(
            organization=organization, trigger_type=trigger_type, team=make_team(organization)
        )

    for trigger_type in Webhook.STATUS_CHANGE_TRIGGERS:
        with patch("apps.webhooks.tasks.trigger_webhook.execute_webhook.apply_async") as mock_execute:
            send_webhook_event(trigger_type, alert_group.pk, organization_id=organization.pk)
        # execute is called for the trigger type itself and the status change trigger too (with the original type passed)
        assert mock_execute.call_count == 2
        mock_execute.assert_any_call(
            (webhooks[trigger_type].pk, alert_group.pk, None, None), kwargs={"trigger_type": trigger_type}
        )
        status_change_trigger_type = Webhook.TRIGGER_STATUS_CHANGE
        mock_execute.assert_any_call(
            (webhooks[status_change_trigger_type].pk, alert_group.pk, None, None), kwargs={"trigger_type": trigger_type}
        )


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
    make_organization, make_team, make_alert_receive_channel, make_alert_group, make_custom_webhook, caplog
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    other_alert_receive_channel = make_alert_receive_channel(organization)
    webhook = make_custom_webhook(
        organization=organization,
        trigger_type=Webhook.TRIGGER_ALERT_GROUP_CREATED,
    )
    webhook.filtered_integrations.add(other_alert_receive_channel)

    with patch("apps.webhooks.models.webhook.WebhookSession.request") as mock_request:
        execute_webhook(webhook.pk, alert_group.pk, None, None)

    assert not mock_request.called
    # no response is created for the webhook
    assert webhook.responses.count() == 0
    # check log should exist
    assert f"Webhook {webhook.pk} was not triggered: {NOT_FROM_SELECTED_INTEGRATION}" in caplog.text


@pytest.mark.django_db
def test_execute_webhook_integration_filter_matching(
    make_organization, make_team, make_alert_receive_channel, make_alert_group, make_custom_webhook, caplog
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization, public_primary_key="test-integration-1")
    alert_group = make_alert_group(alert_receive_channel)
    webhook = make_custom_webhook(
        organization=organization,
        trigger_type=Webhook.TRIGGER_ALERT_GROUP_CREATED,
        # Check we get past integration filter but exit early to keep test simple
        trigger_template="False",
    )
    webhook.filtered_integrations.add(alert_receive_channel)

    with patch("apps.webhooks.models.webhook.WebhookSession.request") as mock_request:
        execute_webhook(webhook.pk, alert_group.pk, None, None)

    assert not mock_request.called
    # no response is created for the webhook
    assert webhook.responses.count() == 0
    # check log should exist
    assert f"Webhook {webhook.pk} was not triggered: False" in caplog.text


ALERT_GROUP_PUBLIC_PRIMARY_KEY = "IXJ47FKMYYJ5U"


@httpretty.activate(verbose=True, allow_net_connect=False)
@pytest.mark.parametrize(
    "data,expected_request_data,request_post_kwargs",
    [
        (
            '{"value": "{{ alert_group_id }}"}',
            json.dumps({"value": ALERT_GROUP_PUBLIC_PRIMARY_KEY}),
            {"json": {"value": ALERT_GROUP_PUBLIC_PRIMARY_KEY}},
        ),
        # test that non-latin characters are properly encoded
        (
            "😊",
            "b'\\xf0\\x9f\\x98\\x8a'",
            {"data": "😊".encode("utf-8")},
        ),
    ],
)
@pytest.mark.django_db
def test_execute_webhook_ok(
    make_organization,
    make_user_for_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_custom_webhook,
    data,
    expected_request_data,
    request_post_kwargs,
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(
        alert_receive_channel,
        acknowledged_at=timezone.now(),
        acknowledged=True,
        acknowledged_by=user.pk,
        public_primary_key=ALERT_GROUP_PUBLIC_PRIMARY_KEY,
    )
    webhook = make_custom_webhook(
        organization=organization,
        url="https://example.com/{{ alert_group_id }}/",
        http_method="POST",
        trigger_type=Webhook.TRIGGER_ACKNOWLEDGE,
        trigger_template="{{{{ alert_group.integration_id == '{}' }}}}".format(
            alert_receive_channel.public_primary_key
        ),
        headers='{"some-header": "{{ alert_group_id }}"}',
        data=data,
        forward_all=False,
    )

    templated_url = f"https://example.com/{alert_group.public_primary_key}/"
    mock_response = httpretty.Response(json.dumps({"response": 200}))
    httpretty.register_uri(httpretty.POST, templated_url, responses=[mock_response])

    with patch("apps.webhooks.utils.socket.gethostbyname", return_value="8.8.8.8"):
        with patch(
            "apps.webhooks.models.webhook.WebhookSession.request", wraps=WebhookSession().request
        ) as mock_request:
            execute_webhook(webhook.pk, alert_group.pk, user.pk, None)

    mock_request.assert_called_once_with(
        "POST",
        templated_url,
        timeout=TIMEOUT,
        headers={"some-header": alert_group.public_primary_key},
        **request_post_kwargs,
    )

    # assert the request was made to the webhook as we expected
    last_request = httpretty.last_request()
    assert last_request.method == "POST"
    assert last_request.url == templated_url
    assert last_request.headers["some-header"] == alert_group.public_primary_key

    # check logs
    log = webhook.responses.all()[0]
    assert log.status_code == 200
    assert log.content == json.dumps({"response": 200})
    assert log.request_data == expected_request_data
    assert log.request_headers == json.dumps({"some-header": alert_group.public_primary_key})
    assert log.url == templated_url
    # check log record
    log_record = alert_group.log_records.last()
    assert log_record.type == AlertGroupLogRecord.TYPE_CUSTOM_WEBHOOK_TRIGGERED
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
        with patch("apps.webhooks.models.webhook.WebhookSession.request", return_value=mock_response) as mock_request:
            execute_webhook(webhook.pk, alert_group.pk, user.pk, escalation_policy.pk)

    assert mock_request.called
    # check log record
    log_record = alert_group.log_records.last()
    assert log_record.type == AlertGroupLogRecord.TYPE_CUSTOM_WEBHOOK_TRIGGERED
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
@pytest.mark.parametrize(
    "webhook_trigger_type",
    [Webhook.TRIGGER_ACKNOWLEDGE, Webhook.TRIGGER_STATUS_CHANGE],
)
def test_execute_webhook_ok_forward_all(
    make_organization,
    make_user_for_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_user_notification_policy_log_record,
    make_custom_webhook,
    webhook_trigger_type,
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    notified_user = make_user_for_organization(organization)
    other_user = make_user_for_organization(organization)
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(
        alert_receive_channel,
        acknowledged_at=timezone.now(),
        acknowledged=True,
        acknowledged_by=user.pk,
        acknowledged_by_user=user,
    )
    for _ in range(3):
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
        trigger_type=webhook_trigger_type,
        forward_all=True,
    )

    mock_response = MockResponse()
    with patch("apps.webhooks.utils.socket.gethostbyname") as mock_gethostbyname:
        mock_gethostbyname.return_value = "8.8.8.8"
        with patch("apps.webhooks.models.webhook.WebhookSession.request", return_value=mock_response) as mock_request:
            execute_webhook(webhook.pk, alert_group.pk, user.pk, None, trigger_type=Webhook.TRIGGER_ACKNOWLEDGE)

    assert mock_request.called
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
            "labels": {},
        },
        "notified_users": [
            {
                "id": notified_user.public_primary_key,
                "username": notified_user.username,
                "email": notified_user.email,
            }
        ],
        "alert_group": {**IncidentSerializer(alert_group).data, "labels": {}},
        "alert_group_id": alert_group.public_primary_key,
        "alert_payload": "",
        "users_to_be_notified": [],
        "webhook": {
            "id": webhook.public_primary_key,
            "name": webhook.name,
            "labels": {},
        },
        "alert_group_acknowledged_by": {
            "id": user.public_primary_key,
            "username": user.username,
            "email": user.email,
        },
        "alert_group_resolved_by": None,
    }
    expected_call = call(
        "POST",
        "https://something/{}/".format(alert_group.public_primary_key),
        timeout=TIMEOUT,
        headers={},
        json=expected_data,
    )
    assert mock_request.call_args == expected_call
    # check logs
    log = webhook.responses.all()[0]
    assert log.trigger_type == Webhook.TRIGGER_ACKNOWLEDGE
    assert log.status_code == 200
    assert log.content == json.dumps(mock_response.json())
    assert json.loads(log.request_data) == expected_data
    assert log.url == "https://something/{}/".format(alert_group.public_primary_key)


@pytest.mark.django_db
def test_execute_webhook_ok_forward_all_resolved(
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
        alert_receive_channel,
        acknowledged_at=timezone.now(),
        acknowledged=True,
        acknowledged_by=user.pk,
        acknowledged_by_user=user,
        resolved=True,
        resolved_at=timezone.now() + timedelta(hours=2),
        resolved_by=user.pk,
        resolved_by_user=user,
    )
    for _ in range(3):
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
        trigger_type=Webhook.TRIGGER_RESOLVE,
        forward_all=True,
    )

    mock_response = MockResponse()
    with patch("apps.webhooks.utils.socket.gethostbyname") as mock_gethostbyname:
        mock_gethostbyname.return_value = "8.8.8.8"
        with patch("apps.webhooks.models.webhook.WebhookSession.request", return_value=mock_response) as mock_request:
            execute_webhook(webhook.pk, alert_group.pk, user.pk, None, trigger_type=Webhook.TRIGGER_RESOLVE)

    assert mock_request.called
    expected_data = {
        "event": {
            "type": "resolve",
            "time": alert_group.resolved_at.isoformat(),
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
            "labels": {},
        },
        "notified_users": [
            {
                "id": notified_user.public_primary_key,
                "username": notified_user.username,
                "email": notified_user.email,
            }
        ],
        "alert_group": {**IncidentSerializer(alert_group).data, "labels": {}},
        "alert_group_id": alert_group.public_primary_key,
        "alert_payload": "",
        "users_to_be_notified": [],
        "webhook": {
            "id": webhook.public_primary_key,
            "name": webhook.name,
            "labels": {},
        },
        "alert_group_acknowledged_by": {
            "id": user.public_primary_key,
            "username": user.username,
            "email": user.email,
        },
        "alert_group_resolved_by": {
            "id": user.public_primary_key,
            "username": user.username,
            "email": user.email,
        },
    }
    expected_call = call(
        "POST",
        "https://something/{}/".format(alert_group.public_primary_key),
        timeout=TIMEOUT,
        headers={},
        json=expected_data,
    )
    assert mock_request.call_args == expected_call
    # check logs
    log = webhook.responses.all()[0]
    assert log.trigger_type == Webhook.TRIGGER_RESOLVE
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
        with patch("apps.webhooks.models.webhook.WebhookSession.request", return_value=mock_response) as mock_request:
            execute_webhook(webhook.pk, alert_group.pk, user.pk, None)

    assert mock_request.called
    expected_data = {"value": "updated"}
    expected_call = call(
        "POST",
        "https://something/third-party-id/",
        timeout=TIMEOUT,
        headers={},
        json=expected_data,
    )
    assert mock_request.call_args == expected_call
    # check logs
    log = webhook.responses.all()[0]
    assert log.status_code == 200
    assert log.content == json.dumps(mock_response.json())
    assert json.loads(log.request_data) == expected_data
    assert log.url == "https://something/third-party-id/"


@pytest.mark.django_db
def test_execute_webhook_trigger_false(
    make_organization, make_alert_receive_channel, make_alert_group, make_custom_webhook, caplog
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

    with patch("apps.webhooks.models.webhook.WebhookSession.request") as mock_request:
        execute_webhook(webhook.pk, alert_group.pk, None, None)

    assert not mock_request.called
    # no response is created for the webhook
    assert webhook.responses.count() == 0
    # check log should exist
    assert f"Webhook {webhook.pk} was not triggered: False" in caplog.text


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
        with patch("apps.webhooks.models.webhook.WebhookSession.request") as mock_request:
            execute_webhook(webhook.pk, alert_group.pk, None, None)

    assert not mock_request.called
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
        with patch("apps.webhooks.models.webhook.WebhookSession.request", return_value=mock_response) as mock_request:
            execute_webhook(webhook.pk, alert_group.pk, user.pk, None)

    assert mock_request.called
    expected_call = call(
        "POST",
        "https://test/",
        timeout=TIMEOUT,
        headers={},
    )
    assert mock_request.call_args == expected_call
    # check logs
    log = webhook.responses.all()[0]
    assert log.status_code == 200
    assert log.content == f"Response content {content_length} exceeds {WEBHOOK_RESPONSE_LIMIT} character limit"
    assert log.url == "https://test/"


@patch("apps.webhooks.tasks.trigger_webhook.execute_webhook", wraps=execute_webhook)
@patch("apps.webhooks.models.webhook.WebhookSession.request")
@patch("apps.webhooks.utils.socket.gethostbyname", return_value="8.8.8.8")
@pytest.mark.django_db
@pytest.mark.parametrize("exception", [requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout])
def test_manually_retried_exceptions(
    _mock_gethostbyname,
    mock_request,
    spy_execute_webhook,
    make_organization,
    make_user_for_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_custom_webhook,
    exception,
):
    mock_request.side_effect = exception("foo bar")

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

    execute_webhook_args = webhook.pk, alert_group.pk, user.pk, None

    # should retry
    execute_webhook(*execute_webhook_args)

    mock_request.assert_called_once_with("POST", "https://test/", timeout=TIMEOUT, headers={})
    spy_execute_webhook.apply_async.assert_called_once_with(
        execute_webhook_args, kwargs={"trigger_type": None, "manual_retry_num": 1}, countdown=10
    )

    mock_request.reset_mock()
    spy_execute_webhook.reset_mock()

    # should stop retrying after 3 attempts without raising issue
    try:
        execute_webhook(*execute_webhook_args, manual_retry_num=3)
    except Exception:
        pytest.fail()

    mock_request.assert_called_once_with("POST", "https://test/", timeout=TIMEOUT, headers={})
    spy_execute_webhook.apply_async.assert_not_called()


@patch("apps.webhooks.models.webhook.WebhookSession.request", return_value=MockResponse())
@patch("apps.webhooks.utils.socket.gethostbyname", return_value="8.8.8.8")
@pytest.mark.django_db
def test_execute_webhook_integration_config(
    _,
    mock_request,
    make_organization,
    make_user_for_organization,
    make_alert_receive_channel,
    make_alert_receive_channel_connection,
    make_alert_group,
    make_user_notification_policy_log_record,
    make_custom_webhook,
):
    organization = make_organization()
    user = make_user_for_organization(organization)

    # create connected integrations
    source_alert_receive_channel = make_alert_receive_channel(
        organization, additional_settings={"must_be": "non_empty"}
    )  # TODO: revisit this
    alert_receive_channel = make_alert_receive_channel(organization)
    make_alert_receive_channel_connection(source_alert_receive_channel, alert_receive_channel)

    alert_group = make_alert_group(alert_receive_channel)
    webhook = make_custom_webhook(
        organization=organization,
        url="https://something/{{ external_id }}",
        http_method="POST",
        trigger_type=Webhook.TRIGGER_ALERT_GROUP_CREATED,
        forward_all=True,
        is_from_connected_integration=True,
    )
    webhook.filtered_integrations.set([source_alert_receive_channel, alert_receive_channel])

    # create external ID entry
    AlertGroupExternalID.objects.create(
        source_alert_receive_channel=source_alert_receive_channel, alert_group=alert_group, value="test123"
    )

    with patch.object(
        source_alert_receive_channel.config,
        "additional_webhook_data",
        create=True,
        return_value={"additional_field": "additional_value"},
    ) as mock_additional_webhook_data:
        with patch.object(
            source_alert_receive_channel.config, "on_webhook_response_created", create=True
        ) as mock_on_webhook_response_created:
            execute_webhook(webhook.pk, alert_group.pk, user.pk, None, trigger_type=Webhook.TRIGGER_ALERT_GROUP_CREATED)

    assert mock_request.called

    # check external ID
    assert mock_request.call_args[0][0] == "POST"
    assert mock_request.call_args[0][1] == "https://something/test123"
    assert mock_request.call_args[1]["json"]["external_id"] == "test123"

    # check additional webhook data
    assert mock_request.call_args[1]["json"]["additional_field"] == "additional_value"
    mock_additional_webhook_data.assert_called_once_with(source_alert_receive_channel)

    # check on_webhook_response_created is called
    mock_on_webhook_response_created.assert_called_once_with(webhook.responses.all()[0], source_alert_receive_channel)
