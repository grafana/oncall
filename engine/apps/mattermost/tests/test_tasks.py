import json
from unittest.mock import patch

import httpretty
import pytest
from django.conf import settings
from django.utils import timezone
from rest_framework import status

from apps.alerts.models import AlertGroupLogRecord
from apps.base.models import UserNotificationPolicyLogRecord
from apps.base.models.user_notification_policy import UserNotificationPolicy
from apps.mattermost.client import MattermostAPIException
from apps.mattermost.models import MattermostMessage
from apps.mattermost.tasks import (
    notify_user_about_alert_async,
    on_alert_group_action_triggered_async,
    on_create_alert_async,
)


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_on_create_alert_async_success(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_mattermost_channel,
    make_mattermost_post_response,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    alert = make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    make_mattermost_channel(organization=organization, is_default_channel=True)

    url = "{}/api/v4/posts".format(settings.MATTERMOST_HOST)
    data = make_mattermost_post_response()
    mock_response = httpretty.Response(json.dumps(data), status=status.HTTP_200_OK)
    httpretty.register_uri(httpretty.POST, url, responses=[mock_response])

    on_create_alert_async(alert_pk=alert.pk)

    mattermost_message = alert_group.mattermost_messages.order_by("created_at").first()
    assert mattermost_message.post_id == data["id"]
    assert mattermost_message.channel_id == data["channel_id"]
    assert mattermost_message.message_type == MattermostMessage.ALERT_GROUP_MESSAGE


@pytest.mark.django_db
def test_on_create_alert_async_skip_post_for_duplicate(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_mattermost_channel,
    make_mattermost_message,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    alert = make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    make_mattermost_channel(organization=organization, is_default_channel=True)
    make_mattermost_message(alert_group, MattermostMessage.ALERT_GROUP_MESSAGE)

    with patch("apps.mattermost.client.MattermostClient.create_post") as mock_post_call:
        on_create_alert_async(alert_pk=alert.pk)

    mock_post_call.assert_not_called()


@pytest.mark.django_db
def test_on_create_alert_async_skip_post_for_no_channel(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_mattermost_message,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    alert = make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    make_mattermost_message(alert_group, MattermostMessage.ALERT_GROUP_MESSAGE)

    with patch("apps.mattermost.client.MattermostClient.create_post") as mock_post_call:
        on_create_alert_async(alert_pk=alert.pk)

    mock_post_call.assert_not_called()


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
@pytest.mark.parametrize("status_code", [400, 401])
def test_on_create_alert_async_mattermost_api_failure(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_mattermost_channel,
    make_mattermost_post_response_failure,
    status_code,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    alert = make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    make_mattermost_channel(organization=organization, is_default_channel=True)

    url = "{}/api/v4/posts".format(settings.MATTERMOST_HOST)
    data = make_mattermost_post_response_failure(status_code=status_code)
    mock_response = httpretty.Response(json.dumps(data), status=status_code)
    httpretty.register_uri(httpretty.POST, url, status=status_code, responses=[mock_response])

    on_create_alert_async(alert_pk=alert.pk)

    mattermost_message = alert_group.mattermost_messages.order_by("created_at").first()
    assert mattermost_message is None


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_on_alert_group_action_triggered_async_success(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_mattermost_channel,
    make_mattermost_post_response,
    make_alert_group_log_record,
    make_mattermost_message,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    ack_alert_group = make_alert_group(alert_receive_channel, acknowledged_at=timezone.now(), acknowledged=True)
    make_alert(alert_group=ack_alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    make_mattermost_channel(organization=organization, is_default_channel=True)
    ack_log_record = make_alert_group_log_record(ack_alert_group, type=AlertGroupLogRecord.TYPE_ACK, author=None)
    mattermost_message = make_mattermost_message(ack_alert_group, MattermostMessage.ALERT_GROUP_MESSAGE)
    expected_button_ids = ["unacknowledge", "resolve"]

    url = "{}/api/v4/posts/{}".format(settings.MATTERMOST_HOST, mattermost_message.post_id)
    data = make_mattermost_post_response()
    mock_response = httpretty.Response(json.dumps(data), status=status.HTTP_200_OK)
    httpretty.register_uri(httpretty.PUT, url, responses=[mock_response])

    on_alert_group_action_triggered_async(ack_log_record.pk)

    last_request = httpretty.last_request()
    assert last_request.method == "PUT"
    assert last_request.url == url

    request_body = json.loads(last_request.body)
    ids = [a["id"] for a in request_body["props"]["attachments"][0]["actions"]]
    for id in ids:
        assert id in expected_button_ids


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_on_alert_group_action_triggered_async_fails_without_alert_group_message(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_mattermost_channel,
    make_alert_group_log_record,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    ack_alert_group = make_alert_group(alert_receive_channel, acknowledged_at=timezone.now(), acknowledged=True)
    make_alert(alert_group=ack_alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    make_mattermost_channel(organization=organization, is_default_channel=True)
    ack_log_record = make_alert_group_log_record(ack_alert_group, type=AlertGroupLogRecord.TYPE_ACK, author=None)

    with pytest.raises(MattermostMessage.DoesNotExist):
        on_alert_group_action_triggered_async(ack_log_record.pk)


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
@pytest.mark.parametrize("status_code", [400, 401])
def test_on_alert_group_action_triggered_async_failure(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_mattermost_channel,
    make_alert_group_log_record,
    make_mattermost_message,
    make_mattermost_post_response_failure,
    status_code,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    ack_alert_group = make_alert_group(alert_receive_channel, acknowledged_at=timezone.now(), acknowledged=True)
    make_alert(alert_group=ack_alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    make_mattermost_channel(organization=organization, is_default_channel=True)
    ack_log_record = make_alert_group_log_record(ack_alert_group, type=AlertGroupLogRecord.TYPE_ACK, author=None)
    mattermost_message = make_mattermost_message(ack_alert_group, MattermostMessage.ALERT_GROUP_MESSAGE)

    url = "{}/api/v4/posts/{}".format(settings.MATTERMOST_HOST, mattermost_message.post_id)
    data = make_mattermost_post_response_failure(status_code=status_code)
    mock_response = httpretty.Response(json.dumps(data), status=status_code)
    httpretty.register_uri(httpretty.PUT, url, status=status_code, responses=[mock_response])

    if status_code != 401:
        with pytest.raises(MattermostAPIException):
            on_alert_group_action_triggered_async(ack_log_record.pk)
    else:
        on_alert_group_action_triggered_async(ack_log_record.pk)

    last_request = httpretty.last_request()
    assert last_request.method == "PUT"
    assert last_request.url == url


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_notify_user_about_alert_async_success(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_mattermost_channel,
    make_mattermost_post_response,
    make_mattermost_message,
    make_user_notification_policy,
    make_mattermost_user,
):
    organization, user = make_organization_and_user()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)

    make_mattermost_channel(organization=organization, is_default_channel=True)
    make_mattermost_message(alert_group, MattermostMessage.ALERT_GROUP_MESSAGE)

    make_mattermost_user(user=user)
    user_notification_policy = make_user_notification_policy(
        user=user,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.TESTONLY,
    )

    url = "{}/api/v4/posts".format(settings.MATTERMOST_HOST)
    data = make_mattermost_post_response()
    mock_response = httpretty.Response(json.dumps(data), status=status.HTTP_200_OK)
    httpretty.register_uri(httpretty.POST, url, responses=[mock_response])

    notify_user_about_alert_async(
        user_pk=user.pk, alert_group_pk=alert_group.pk, notification_policy_pk=user_notification_policy.pk
    )

    mattermost_message = alert_group.mattermost_messages.order_by("created_at").last()
    assert mattermost_message.post_id == data["id"]
    assert mattermost_message.channel_id == data["channel_id"]
    assert mattermost_message.message_type == MattermostMessage.USER_NOTIFACTION_MESSAGE


@pytest.mark.django_db
def test_notify_user_about_alert_async_user_does_not_exist(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_mattermost_channel,
    make_mattermost_message,
    make_mattermost_user,
    make_user_notification_policy,
):
    organization, user = make_organization_and_user()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    make_mattermost_channel(organization=organization, is_default_channel=True)
    make_mattermost_message(alert_group, MattermostMessage.ALERT_GROUP_MESSAGE)
    make_mattermost_user(user=user)
    user_notification_policy = make_user_notification_policy(
        user=user,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.TESTONLY,
    )

    with patch("apps.mattermost.client.MattermostClient.create_post") as mock_post_call:
        notify_user_about_alert_async(
            user_pk=123, alert_group_pk=alert_group.pk, notification_policy_pk=user_notification_policy.pk
        )

    mock_post_call.assert_not_called()


@pytest.mark.django_db
def test_notify_user_about_alert_async_alert_does_not_exist(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_mattermost_channel,
    make_mattermost_message,
    make_mattermost_user,
    make_user_notification_policy,
):
    organization, user = make_organization_and_user()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    make_mattermost_channel(organization=organization, is_default_channel=True)
    make_mattermost_message(alert_group, MattermostMessage.ALERT_GROUP_MESSAGE)
    make_mattermost_user(user=user)
    user_notification_policy = make_user_notification_policy(
        user=user,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.TESTONLY,
    )

    with patch("apps.mattermost.client.MattermostClient.create_post") as mock_post_call:
        notify_user_about_alert_async(
            user_pk=user.pk, alert_group_pk=123, notification_policy_pk=user_notification_policy.pk
        )

    mock_post_call.assert_not_called()


@pytest.mark.django_db
def test_notify_user_about_alert_async_notification_policy_does_not_exist(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_mattermost_channel,
    make_mattermost_message,
    make_mattermost_user,
):
    organization, user = make_organization_and_user()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    make_mattermost_channel(organization=organization, is_default_channel=True)
    make_mattermost_message(alert_group, MattermostMessage.ALERT_GROUP_MESSAGE)
    make_mattermost_user(user=user)

    with patch("apps.mattermost.client.MattermostClient.create_post") as mock_post_call:
        notify_user_about_alert_async(user_pk=user.pk, alert_group_pk=alert_group.pk, notification_policy_pk=123)

    mock_post_call.assert_not_called()


@pytest.mark.django_db
def test_notify_user_about_alert_async_mattermost_message_does_not_exist(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_mattermost_channel,
    make_mattermost_user,
    make_user_notification_policy,
):
    organization, user = make_organization_and_user()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    make_mattermost_channel(organization=organization, is_default_channel=True)
    make_mattermost_user(user=user)
    user_notification_policy = make_user_notification_policy(
        user=user,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.TESTONLY,
    )

    with pytest.raises(MattermostMessage.DoesNotExist):
        notify_user_about_alert_async(
            user_pk=user.pk, alert_group_pk=alert_group.pk, notification_policy_pk=user_notification_policy.pk
        )


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_notify_user_about_alert_async_mattermost_user_does_not_exist(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_mattermost_channel,
    make_mattermost_message,
    make_user_notification_policy,
    make_mattermost_post_response,
):
    organization, user = make_organization_and_user()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    make_mattermost_channel(organization=organization, is_default_channel=True)
    make_mattermost_message(alert_group, MattermostMessage.ALERT_GROUP_MESSAGE)
    user_notification_policy = make_user_notification_policy(
        user=user,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.TESTONLY,
    )

    url = "{}/api/v4/posts".format(settings.MATTERMOST_HOST)
    data = make_mattermost_post_response()
    mock_response = httpretty.Response(json.dumps(data), status=status.HTTP_200_OK)
    httpretty.register_uri(httpretty.POST, url, responses=[mock_response])

    notify_user_about_alert_async(
        user_pk=user.pk, alert_group_pk=alert_group.pk, notification_policy_pk=user_notification_policy.pk
    )

    log_record = user_notification_policy.personal_log_records.last()
    mattermost_message = alert_group.mattermost_messages.order_by("created_at").last()
    assert mattermost_message.post_id == data["id"]
    assert mattermost_message.channel_id == data["channel_id"]
    assert mattermost_message.message_type == MattermostMessage.USER_NOTIFACTION_MESSAGE
    assert (
        log_record.notification_error_code
        == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_MATTERMOST_USER_NOT_IN_MATTERMOST
    )


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
@pytest.mark.parametrize("status_code", [400, 401])
def test_notify_user_about_alert_async_api_failure(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_mattermost_channel,
    make_mattermost_message,
    make_mattermost_post_response_failure,
    make_user_notification_policy,
    make_mattermost_user,
    status_code,
):
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    make_mattermost_channel(organization=organization, is_default_channel=True)
    make_mattermost_message(alert_group, MattermostMessage.ALERT_GROUP_MESSAGE)
    make_mattermost_user(user=user)
    user_notification_policy = make_user_notification_policy(
        user=user,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.TESTONLY,
    )

    url = "{}/api/v4/posts".format(settings.MATTERMOST_HOST)
    data = make_mattermost_post_response_failure(status_code=status_code)
    mock_response = httpretty.Response(json.dumps(data), status=status_code)
    httpretty.register_uri(httpretty.POST, url, status=status_code, responses=[mock_response])

    if status_code != 401:
        with pytest.raises(MattermostAPIException):
            notify_user_about_alert_async(
                user_pk=user.pk, alert_group_pk=alert_group.pk, notification_policy_pk=user_notification_policy.pk
            )
    else:
        notify_user_about_alert_async(
            user_pk=user.pk, alert_group_pk=alert_group.pk, notification_policy_pk=user_notification_policy.pk
        )

    last_request = httpretty.last_request()
    assert last_request.method == "POST"
    assert last_request.url == url


@pytest.mark.django_db
def test_notify_user_about_alert_async_skip_post_for_no_channel(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_mattermost_message,
    make_mattermost_user,
    make_user_notification_policy,
):
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    make_mattermost_message(alert_group, MattermostMessage.ALERT_GROUP_MESSAGE)
    make_mattermost_user(user=user)
    user_notification_policy = make_user_notification_policy(
        user=user,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.TESTONLY,
    )

    with patch("apps.mattermost.client.MattermostClient.create_post") as mock_post_call:
        notify_user_about_alert_async(
            user_pk=user.pk, alert_group_pk=alert_group.pk, notification_policy_pk=user_notification_policy.pk
        )

    mock_post_call.assert_not_called()
